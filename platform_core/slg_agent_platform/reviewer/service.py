"""ReviewerService — the authenticated human-approval decision.

Replaces the mint_approval.py stand-in. A reviewer presents a verified identity (JWT claims
from the Cognito authorizer) and a decision (approve|reject) on a SPECIFIC pending approval.
The service enforces the controls the stand-in could not:

  1. Authority   — the reviewer must be ENTITLED to the tool being approved
                   (policy.user_entitlements): you can only approve an action you are
                   yourself authorized to perform. (Production may require a strictly
                   higher approver tier; the entitlement check is the floor.)
  2. Separation of duties — the reviewer's subject MUST differ from the requestor.
  3. Single use  — the pending record is CLAIMED atomically (PENDING -> APPROVED/REJECTED);
                   a replayed or double approval is rejected by the store.
  4. Server-side secret — the bound token is minted HERE (approvals.mint_approval_token),
                   so the reviewer never holds the signing key. The minted token is bound to
                   requestor+agent+tool+args_hash, so it cannot be retargeted or tampered.
  5. Resume      — on approve, the paused Step Functions task is resumed with the token via
                   SendTaskSuccess; on reject, SendTaskFailure ends the execution cleanly.
  6. Audit       — every decision (granted / rejected / DENIED-unauthorized) is written to
                   the append-only audit log with the reviewer, requestor, tool, and reason.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from slg_agent_platform.mcp_gateway import approvals, policy
from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog
from slg_agent_platform.mcp_gateway.gateway import _roles_from_claims
from .store import ClaimConflict, PendingApprovalStore


class ReviewerError(Exception):
    """Reviewer decision could not be completed (not found, unauthorized, already resolved)."""


@dataclass
class PendingApproval:
    approval_id: str
    task_token: str
    agent_id: str
    requestor: str
    tool: str
    args: Dict[str, Any]


class _Boto3StepFunctions:  # pragma: no cover - requires boto3 + AWS
    """Thin wrapper so the service depends on a tiny interface, not boto3 directly."""

    def __init__(self, client: Any = None) -> None:
        import boto3
        self._sf = client or boto3.client("stepfunctions")

    def send_task_success(self, task_token: str, output: Dict[str, Any]) -> None:
        self._sf.send_task_success(taskToken=task_token, output=json.dumps(output))

    def send_task_failure(self, task_token: str, error: str, cause: str) -> None:
        self._sf.send_task_failure(taskToken=task_token, error=error, cause=cause)


class ReviewerService:
    def __init__(self, store: PendingApprovalStore, sfn: Any = None,
                 audit: Optional[GatewayAuditLog] = None) -> None:
        self._store = store
        self._sfn = sfn  # interface with send_task_success / send_task_failure
        self._audit = audit or GatewayAuditLog()

    # ── queue the reviewer sees ───────────────────────────────────────────────
    def list_pending(self, reviewer_claims: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Open approvals this reviewer is allowed to act on (authority + SoD pre-filtered)."""
        sub = (reviewer_claims or {}).get("sub")
        ent = policy.user_entitlements(_roles_from_claims(reviewer_claims or {}))
        out = []
        for r in self._store.list_pending():
            if r.get("tool") in ent and r.get("requestor") != sub:
                out.append({k: r.get(k) for k in
                            ("approval_id", "agent_id", "requestor", "tool", "args", "created_at")})
        return out

    # ── the decision ──────────────────────────────────────────────────────────
    def decide(self, reviewer_claims: Dict[str, Any], approval_id: str, decision: str,
               *, comment: str = "") -> Dict[str, Any]:
        decision = (decision or "").strip().lower()
        if decision not in ("approve", "reject"):
            raise ReviewerError("decision must be 'approve' or 'reject'")

        reviewer_sub = (reviewer_claims or {}).get("sub")
        reviewer_roles = _roles_from_claims(reviewer_claims or {})
        if not reviewer_sub:
            raise ReviewerError("unauthenticated reviewer (no subject)")

        row = self._store.get(approval_id)
        if not row or row.get("status") != "PENDING":
            raise ReviewerError("approval not found or already resolved")

        tool = row["tool"]
        requestor = row["requestor"]

        # 1) separation of duties + 2) authority over the tool — checked BEFORE any claim.
        if reviewer_sub == requestor:
            self._record("APPROVAL_DENIED", row, reviewer_sub, reviewer_roles,
                         "separation of duties: reviewer is the requestor")
            raise ReviewerError("separation of duties: a reviewer cannot approve their own request")
        if tool not in policy.user_entitlements(reviewer_roles):
            self._record("APPROVAL_DENIED", row, reviewer_sub, reviewer_roles,
                         f"reviewer not entitled to approve {tool}")
            raise ReviewerError(f"reviewer is not authorized to approve {tool}")

        # 3) single-use: claim the record atomically (PENDING -> APPROVED/REJECTED).
        new_status = "APPROVED" if decision == "approve" else "REJECTED"
        try:
            self._store.claim(approval_id, new_status, by=reviewer_sub)
        except ClaimConflict as exc:
            raise ReviewerError(str(exc)) from exc

        if decision == "reject":
            if self._sfn is not None:
                self._sfn.send_task_failure(row["task_token"], "REJECTED_BY_REVIEWER",
                                            comment or "rejected at human gate")
            self._record("APPROVAL_REJECTED", row, reviewer_sub, reviewer_roles, comment or "rejected")
            return {"status": "REJECTED", "approval_id": approval_id}

        # 4) approve: mint the bound token SERVER-SIDE (reviewer never holds the secret).
        token = approvals.mint_approval_token(
            requestor=requestor, agent_id=row["agent_id"], tool=tool,
            args=row.get("args", {}), approver=reviewer_sub)
        # 5) resume the paused execution with the token.
        if self._sfn is not None:
            self._sfn.send_task_success(
                row["task_token"],
                {"token": token, "reviewer": {"sub": reviewer_sub, "roles": reviewer_roles},
                 "comment": comment})
        # 6) audit the grant.
        audit_id = self._record("APPROVAL_GRANTED", row, reviewer_sub, reviewer_roles,
                                comment or "approved at human gate")
        return {"status": "APPROVED", "approval_id": approval_id, "audit_id": audit_id,
                "token": token}

    def _record(self, decision: str, row: Dict[str, Any], reviewer_sub: str,
                reviewer_roles: List[str], reason: str) -> str:
        return self._audit.record({
            "event": "human_approval_decision",
            "decision": decision,
            "agent_id": row.get("agent_id"),
            "tool": row.get("tool"),
            "requestor": row.get("requestor"),
            "approver": reviewer_sub,
            "approver_roles": reviewer_roles,
            "args": row.get("args", {}),
            "reason": reason,
        })
