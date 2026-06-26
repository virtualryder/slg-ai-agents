"""
Govern Tool Access — the government tool gateway.

The deny-by-default MCP gateway (slg_agent_platform) answers "may this agent, on
this user's authority, call this tool?". A whole-of-government deployment needs
MORE than that before a tool may touch a system of record. Every governed tool
declares a full contract:

  * agency            — which agency owns the tool / system of record
  * purposes          — the allowed purposes of use (purpose binding; a benefits
                        tool used for a fraud sweep is a different, separately
                        consented purpose)
  * data_classes      — CJI | FTI | PHI | EDU | PII | PUBLIC (drives isolation,
                        residency, and retention)
  * residency         — "us" | "us-gov"  (must match the deployment boundary)
  * read_write        — read | write
  * max_amount        — transaction threshold above which a higher gate applies
  * requires_approval — human approval required (derived from gateway high-risk)
  * idempotency       — writes are deduplicated by idempotency key (exactly-once)
  * rollback          — a compensation handler name for the saga coordinator
  * audit             — always on (the underlying gateway audits every attempt)

GovernedToolGateway enforces the contract THEN delegates to the MCP gateway, so
the deny-by-default / least-privilege / scoped-token / audit guarantees still
hold underneath. In production this maps to AgentCore Gateway targets + Amazon
Verified Permissions (Cedar) policies for purpose/threshold/residency, with
EventBridge carrying the audit/compliance events.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from slg_agent_platform.mcp_gateway import MCPGateway, policy


# ── Data classes drive isolation, residency, and retention ────────────────────
DATA_CLASSES = {"CJI", "FTI", "PHI", "EDU", "PII", "PUBLIC"}


@dataclass(frozen=True)
class GovernedTool:
    tool: str                              # "<kind>.<method>" — must exist in TOOL_REGISTRY
    agency: str
    purposes: frozenset                    # allowed purposes of use
    data_classes: tuple = ("PII",)
    residency: str = "us"                  # us | us-gov
    max_amount: Optional[float] = None     # transaction threshold (None = N/A)
    rollback: Optional[str] = None         # compensation handler name (saga)

    @property
    def read_write(self) -> str:
        _, _, high_risk = policy.TOOL_REGISTRY.get(self.tool, ("", "", False))
        return "write" if high_risk else "read"

    @property
    def requires_approval(self) -> bool:
        return self.tool in policy.HIGH_RISK_TOOLS


@dataclass
class GovernResult:
    allowed: bool
    decision: str                          # ALLOW | DENY | PENDING_APPROVAL | DEDUP
    tool: str
    reason: str = ""
    result: Any = None
    governance: Dict[str, Any] = field(default_factory=dict)
    audit_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ToolCatalog:
    """Registry of governed tools. Every cross-agency tool MUST be registered."""

    def __init__(self) -> None:
        self._tools: Dict[str, GovernedTool] = {}

    def register(self, gt: GovernedTool) -> None:
        if gt.tool not in policy.TOOL_REGISTRY:
            raise ValueError(f"{gt.tool!r} is not a real gateway tool (TOOL_REGISTRY)")
        if not set(gt.data_classes) <= DATA_CLASSES:
            raise ValueError(f"unknown data class in {gt.data_classes}")
        self._tools[gt.tool] = gt

    def get(self, tool: str) -> Optional[GovernedTool]:
        return self._tools.get(tool)

    @property
    def tools(self) -> List[GovernedTool]:
        return list(self._tools.values())


class GovernedToolGateway:
    """
    Enforces the governance contract, then delegates to the MCP gateway.

    Order: catalog registration -> purpose binding -> residency -> transaction
    threshold -> idempotency dedupe -> MCPGateway (deny-by-default + approval +
    scoped token + audit) -> register rollback for the saga on a successful write.
    Fail-closed at every step.
    """

    def __init__(self, catalog: ToolCatalog, gateway: Optional[MCPGateway] = None,
                 deployment_residency: Optional[str] = None) -> None:
        self.catalog = catalog
        self.gateway = gateway or MCPGateway(connector_mode="fixture")
        self.residency = deployment_residency or os.getenv("DEPLOYMENT_RESIDENCY", "us")
        self._idem_seen: Dict[str, GovernResult] = {}
        self._rollbacks: List[Dict[str, Any]] = []  # completed writes available to compensate

    def invoke(self, *, user_claims: Dict[str, Any], agent_id: str, tool: str,
               purpose: str, args: Optional[Dict[str, Any]] = None,
               amount: Optional[float] = None, approval: Optional[Dict[str, Any]] = None,
               idempotency_key: Optional[str] = None) -> GovernResult:
        args = args or {}
        gt = self.catalog.get(tool)
        if gt is None:
            return GovernResult(False, "DENY", tool, reason=f"{tool!r} is not in the governed catalog")

        gov = {"agency": gt.agency, "purpose": purpose, "data_classes": list(gt.data_classes),
               "residency": gt.residency, "read_write": gt.read_write}

        # 1. Purpose binding
        if purpose not in gt.purposes:
            return GovernResult(False, "DENY", tool,
                                reason=f"purpose {purpose!r} not permitted for {tool!r} "
                                       f"(allowed: {sorted(gt.purposes)})", governance=gov)
        # 2. Residency must match the deployment boundary
        if gt.residency != self.residency:
            return GovernResult(False, "DENY", tool,
                                reason=f"residency {gt.residency!r} != deployment {self.residency!r}",
                                governance=gov)
        # 3. Transaction threshold
        if gt.max_amount is not None and amount is not None and amount > gt.max_amount:
            return GovernResult(False, "DENY", tool,
                                reason=f"amount {amount} exceeds threshold {gt.max_amount} "
                                       f"(requires a higher human gate)", governance=gov)
        # 4. Idempotency — exactly-once for writes
        if idempotency_key and idempotency_key in self._idem_seen:
            prior = self._idem_seen[idempotency_key]
            return GovernResult(prior.allowed, "DEDUP", tool, reason="idempotent replay suppressed",
                                result=prior.result, governance=gov, idempotency_key=idempotency_key)

        # 5. Delegate to the deny-by-default MCP gateway (authz + approval + token + audit)
        bound_approval = self._bind_approval(
            approval, requestor=user_claims.get("sub", ""),
            agent_id=agent_id, tool=tool, args=args,
        )
        res = self.gateway.invoke(user_claims=user_claims, agent_id=agent_id, tool=tool,
                                  args=args, approval=bound_approval)
        out = GovernResult(res.allowed, res.decision, tool, reason=res.reason, result=res.result,
                           governance=gov, audit_id=res.audit_id, idempotency_key=idempotency_key)

        # 6. On a successful write, register a rollback the saga can invoke
        if res.allowed and gt.read_write == "write":
            self._rollbacks.append({"tool": tool, "rollback": gt.rollback, "args": args,
                                    "agency": gt.agency, "result": res.result})
        if idempotency_key and res.allowed:
            self._idem_seen[idempotency_key] = out
        return out

    @staticmethod
    def _bind_approval(
        approval: Optional[Dict[str, Any]], *, requestor: str, agent_id: str,
        tool: str, args: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Convert a legacy approval dict into a bound approval token."""
        if not approval:
            return None
        if "token" in approval:
            return approval
        from slg_agent_platform.mcp_gateway import approvals as _approvals
        approver = (approval.get("reviewer") or {}).get("sub") or approval.get("approver", "")
        if not approver or not approval.get("approved", False):
            return None
        token = _approvals.mint_approval_token(
            requestor=requestor, agent_id=agent_id, tool=tool,
            args=args, approver=approver,
        )
        return {"token": token}

    @property
    def rollbacks(self) -> List[Dict[str, Any]]:
        return list(self._rollbacks)


def default_catalog() -> ToolCatalog:
    """A starter catalog covering the cross-agency tools used by the life-event demos."""
    c = ToolCatalog()
    reg = [
        GovernedTool("crm311.create_service_request", "311",
                     frozenset({"service_request", "moving", "disaster", "bereavement"}),
                     data_classes=("PII",), rollback="crm311.cancel_service_request"),
        GovernedTool("scheduling.book_appointment", "City Clerk", frozenset({"appointment", "moving"}),
                     data_classes=("PII",), rollback="scheduling.cancel_appointment"),
        GovernedTool("idp.assemble_form", "Shared Services",
                     frozenset({"form", "moving", "new_business", "job_loss", "disaster", "bereavement"}),
                     data_classes=("PII", "FTI"), residency="us"),
        GovernedTool("permitting.create_application", "Permitting", frozenset({"permit", "new_business"}),
                     data_classes=("PII",), rollback="permitting.withdraw_application"),
        GovernedTool("eligibility.create_application", "HHS",
                     frozenset({"benefits", "job_loss", "disaster", "bereavement"}),
                     data_classes=("PII", "PHI", "FTI"), rollback="eligibility.withdraw_application"),
        GovernedTool("eligibility.generate_notice", "HHS", frozenset({"benefits", "job_loss", "disaster"}),
                     data_classes=("PII", "PHI")),
        GovernedTool("records.assemble_package", "Records", frozenset({"bereavement", "records_request"}),
                     data_classes=("PII",), rollback="records.void_package"),
        GovernedTool("consent.record", "Identity",
                     frozenset({"moving", "new_business", "job_loss", "disaster", "bereavement"}),
                     data_classes=("PII",)),
    ]
    for gt in reg:
        c.register(gt)
    return c
