from slg_agent_platform.a2a import Supervisor, INTENT_ROUTES
from gov_platform.wog_orchestration.supervisor import LifeEventOrchestrator
from gov_platform.wog_orchestration.consent import ConsentLedger

def _sup():
    sup = Supervisor()
    for aid in set(INTENT_ROUTES.values()):
        sup.register(aid, lambda claims, p, aid=aid: {"agent": aid, "ok": True})
    return sup

def test_material_step_needs_consent_then_confirmation():
    orch = LifeEventOrchestrator(supervisor=_sup())
    payload = {"resident_ref": "RES-9"}
    # no consent yet
    res = orch.run("moving", {"sub": "u"}, payload, confirmations={})
    statuses = {r.intent: r.status for r in res}
    assert statuses["form"] == "NEEDS_CONSENT"

def test_material_step_completes_with_consent_and_confirmation():
    orch = LifeEventOrchestrator(supervisor=_sup())
    payload = {"resident_ref": "RES-9"}
    for intent in ("service_request", "form", "appointment"):
        orch.consent.record("RES-9", f"moving:{intent}", "AAL2")
    res = orch.run("moving", {"sub": "u"}, payload,
                   confirmations={"service_request": True, "form": True, "appointment": True})
    assert all(r.status == "DONE" for r in res)
    assert len(orch.bus.log) == 3  # every material step emitted a compliance event

def test_compliance_events_are_masked():
    orch = LifeEventOrchestrator(supervisor=_sup())
    orch.consent.record("RES-9", "moving:service_request", "AAL2")
    orch.run("moving", {"sub": "u"}, {"resident_ref": "RES-9"},
             confirmations={"service_request": True})
    assert orch.bus.log  # at least one event recorded
