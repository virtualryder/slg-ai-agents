"""Step Lambda — executes one governed write and emits a committed compliance
event. Raises on a denied/failed write so the Step Functions Catch fires."""
from __future__ import annotations
from typing import Any, Dict, Optional
import _shared
from gov_platform.wog_orchestration.events import ComplianceEvent


def _mint_bound_approval(
    approval: Optional[Dict[str, Any]], *, requestor: str, agent_id: str,
    tool: str, args: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Convert an approval intent into a bound token for this specific tool call."""
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


def handler(event: Dict[str, Any], _ctx=None) -> Dict[str, Any]:
    import _shared as _s
    if _s.GOVGW is None:
        _s.bootstrap()
    spec = event["spec"]; claims = event["claims"]; approval = event.get("approval")
    key = spec.get("idempotency_key", "")
    if _shared.IDEMPOTENCY is not None and key and _shared.IDEMPOTENCY.seen(key):
        return {"name": spec["name"], "status": "SKIPPED_IDEMPOTENT",
                "compensate_tool": spec.get("compensate_tool")}
    # Mint a bound approval token for this specific tool/args if we have an approval intent
    bound_approval = _mint_bound_approval(
        approval, requestor=claims.get("sub", ""),
        agent_id=spec["agent_id"], tool=spec["tool"], args=spec.get("args", {}),
    )
    res = _shared.GOVGW.invoke(user_claims=claims, agent_id=spec["agent_id"], tool=spec["tool"],
                       purpose=spec["purpose"], args=spec.get("args", {}), approval=bound_approval,
                       idempotency_key=spec.get("idempotency_key", ""))
    if not res.allowed and res.decision != "DEDUP":
        raise RuntimeError(f"step {spec['name']} failed: {res.reason}")
    _shared.BUS.publish(ComplianceEvent(
        event_type=f"{event['event']}.{spec['intent']}.committed", resident_ref=event["resident_ref"],
        agency=spec["agency"], agent_id=spec["intent"], data_classes=spec.get("data_classes", ["PII"]),
        human_approval={"confirmed": True}, correlation_id=event.get("correlation_id", ""),
        detail=f"{spec['name']} committed"))
    return {"name": spec["name"], "status": "DONE", "result": res.result,
            "compensate_tool": spec.get("compensate_tool")}
