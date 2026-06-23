"""
Local Step Functions runner — emulates the lifeevent_saga.asl.json control flow
over the real gate/step/compensate Lambda handlers, end-to-end, with NO AWS.

This is the runnable proof of the deployable saga: the SAME declarative life-event
templates, the SAME governed gateway, the SAME compliance events — executed
through the exact Lambda handlers Step Functions would invoke. The control flow
here mirrors the ASL: sequential Map (MaxConcurrency 1) of [Gate -> Step], with a
top-level Catch that routes to Compensate (reverse-order rollback of committed
compensable steps).

Run: PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py
"""
from __future__ import annotations
import sys, uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_HERE / "lambdas")]

import _shared                                                       # noqa: E402
import gate, step, compensate                                       # noqa: E402
from gov_platform.wog_orchestration.consent import ConsentLedger    # noqa: E402
from gov_platform.wog_orchestration.events import ComplianceEventBus, assemble_evidence  # noqa: E402
from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway, GovernResult  # noqa: E402
from gov_platform.wog_orchestration.saga import LIFE_EVENT_TEMPLATES  # noqa: E402

CLAIMS = {"sub": "res-self",
          "custom:slg_role": "INTAKE_SPECIALIST,RESIDENT_SERVICES_AGENT,RECORDS_TECH,"
                             "ELIGIBILITY_CASEWORKER,PERMIT_TECH"}
APPROVE = {"approved": True, "reviewer": {"sub": "supervisor"}}


def run_execution(event: str, resident_ref: str = "RES-55021",
                  confirmations: Optional[Dict[str, bool]] = None,
                  fail_tool: Optional[str] = None) -> Dict[str, Any]:
    consent = ConsentLedger(); bus = ComplianceEventBus()
    govgw = GovernedToolGateway(default_catalog())
    if fail_tool:
        orig = govgw.invoke
        govgw.invoke = lambda **kw: (GovernResult(False, "DENY", fail_tool, reason="agency system unavailable")
                                     if kw.get("tool") == fail_tool else orig(**kw))
    _shared.init(consent, bus, govgw)
    for spec in LIFE_EVENT_TEMPLATES[event]:
        consent.record(resident_ref, f"{event}:{spec.intent}", "AAL2")
    if confirmations is None:
        confirmations = {s.intent: True for s in LIFE_EVENT_TEMPLATES[event]}
    cid = f"{event.upper()}-{uuid.uuid4().hex[:6]}"

    base = {"event": event, "claims": CLAIMS, "approval": APPROVE,
            "resident_ref": resident_ref, "correlation_id": cid, "confirmations": confirmations}
    committed: List[Dict[str, Any]] = []
    outcomes: List[Dict[str, Any]] = []

    # ── Map state (sequential) : [Gate -> Step] per spec ──────────────────────
    for spec in LIFE_EVENT_TEMPLATES[event]:
        item = {**base, "spec": spec.to_dict()}
        gated = gate.handler(item)
        if not gated.get("proceed"):
            outcomes.append({"name": spec.name, "status": "PAUSED", "reason": gated.get("reason")})
            return {"status": "PENDING_GATE", "outcomes": outcomes,
                    "evidence": assemble_evidence(bus, resident_ref, cid).to_audit_dict()}
        try:
            out = step.handler(item)                         # Task: Step
            committed.append(out); outcomes.append(out)
        except Exception as exc:                              # Catch -> Compensate
            outcomes.append({"name": spec.name, "status": "FAILED", "reason": str(exc)})
            comp = compensate.handler({**base, "committed": committed})
            outcomes.append({"name": "Compensate", "status": "DONE", "rolled_back": comp["rolled_back"]})
            return {"status": "COMPENSATED", "outcomes": outcomes, "rolled_back": comp["rolled_back"],
                    "evidence": assemble_evidence(bus, resident_ref, cid).to_audit_dict()}

    return {"status": "COMPLETED", "outcomes": outcomes,
            "evidence": assemble_evidence(bus, resident_ref, cid).to_audit_dict()}


def _print(event, r):
    print(f"\n=== [Step Functions] {event}  ->  {r['status']} ===")
    for o in r["outcomes"]:
        extra = o.get("reason") or (("rolled_back=" + str(o.get("rolled_back"))) if "rolled_back" in o else "")
        print(f"  {o['name']:16s} {o['status']}  {extra}")
    ev = r["evidence"]
    print(f"  evidence: {ev['event_count']} events · {ev['data_classes']} · "
          f"retain {ev['binding_retention_days']}d · compensated={ev['was_compensated']}")


if __name__ == "__main__":
    for ev in ("moving", "job_loss", "new_business", "disaster", "bereavement"):
        _print(ev, run_execution(ev))
    _print("moving(FAIL@book_appt)", run_execution("moving", fail_tool="scheduling.book_appointment"))
    _print("job_loss(no-confirm)", run_execution("job_loss", confirmations={}))
