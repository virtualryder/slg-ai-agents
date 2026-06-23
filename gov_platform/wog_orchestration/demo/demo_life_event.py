"""
Whole-of-Government life-event demo (no API key, no AWS).

Runs THREE life-events from the shared declarative templates, each as a durable
cross-agency saga with govern-tool-access, consent + confirmation gates,
idempotency, compliance events, and compensation:

  moving       -> Shared Services (COA form) -> 311 (request) -> City Clerk (appt)
  job_loss     -> Shared Services (UI form)  -> HHS (benefits app) -> HHS (RFI notice)
  new_business -> Shared Services (reg form) -> Permitting (business permit)

Then re-runs `moving` with an injected 311 outage to show automatic rollback.

Run:  PYTHONPATH=platform_core:. python gov_platform/wog_orchestration/demo/demo_life_event.py
"""
from __future__ import annotations
import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO)]

from gov_platform.wog_orchestration.consent import ConsentLedger          # noqa: E402
from gov_platform.wog_orchestration.events import ComplianceEventBus, assemble_evidence  # noqa: E402
from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway   # noqa: E402
from gov_platform.wog_orchestration.saga import (SagaCoordinator, build_saga,             # noqa: E402
                                                 LIFE_EVENT_TEMPLATES)

CLAIMS = {"sub": "res-self",
          "custom:slg_role": "INTAKE_SPECIALIST,RESIDENT_SERVICES_AGENT,RECORDS_TECH,"
                             "ELIGIBILITY_CASEWORKER,PERMIT_TECH"}
APPROVE = {"approved": True, "reviewer": {"sub": "supervisor", "name": "Supervisor"}}
RES = "RES-55021"


def _seed_consent(event, led):
    for spec in LIFE_EVENT_TEMPLATES[event]:
        led.record(RES, f"{event}:{spec.intent}", "AAL2")


def run(event, fail_tool=None):
    led = ConsentLedger(); bus = ComplianceEventBus(); _seed_consent(event, led)
    govgw = GovernedToolGateway(default_catalog())
    if fail_tool:                                   # simulate an agency outage
        orig = govgw.invoke
        def patched(**kw):
            if kw.get("tool") == fail_tool:
                from gov_platform.wog_orchestration.govern import GovernResult
                return GovernResult(False, "DENY", fail_tool, reason="agency system unavailable")
            return orig(**kw)
        govgw.invoke = patched
    saga = build_saga(event, govgw, RES, APPROVE)
    confirmations = {spec.intent: True for spec in LIFE_EVENT_TEMPLATES[event]}
    res = SagaCoordinator(consent=led, bus=bus).run(saga, CLAIMS, {"resident_ref": RES}, confirmations)
    pkg = assemble_evidence(bus, RES)
    print(f"\n=== {event}{' (FAILURE: '+fail_tool+')' if fail_tool else ''} ===")
    for o in res.outcomes:
        print(f"  {o.name:16s} {o.status}{(' — '+o.reason) if o.reason else ''}")
    print(f"  STATUS={res.status} compensated={res.compensated_steps} | "
          f"evidence: {len(pkg.events)} events · {sorted(set(pkg.data_classes))} · "
          f"retain {pkg.binding_retention_days}d · compensated={pkg.was_compensated}")


if __name__ == "__main__":
    for ev in ("moving", "job_loss", "new_business", "disaster", "bereavement"):
        run(ev)
    run("moving", fail_tool="scheduling.book_appointment")
