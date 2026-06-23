"""Step Lambda — executes one governed write and emits a committed compliance
event. Raises on a denied/failed write so the Step Functions Catch fires."""
from __future__ import annotations
from typing import Any, Dict
import _shared
from gov_platform.wog_orchestration.events import ComplianceEvent


def handler(event: Dict[str, Any], _ctx=None) -> Dict[str, Any]:
    import _shared as _s
    if _s.GOVGW is None:
        _s.bootstrap()
    spec = event["spec"]; claims = event["claims"]; approval = event.get("approval")
    key = spec.get("idempotency_key", "")
    if _shared.IDEMPOTENCY is not None and key and _shared.IDEMPOTENCY.seen(key):
        return {"name": spec["name"], "status": "SKIPPED_IDEMPOTENT",
                "compensate_tool": spec.get("compensate_tool")}
    res = _shared.GOVGW.invoke(user_claims=claims, agent_id=spec["agent_id"], tool=spec["tool"],
                       purpose=spec["purpose"], args=spec.get("args", {}), approval=approval,
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
