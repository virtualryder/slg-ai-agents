from gov_platform.wog_orchestration.saga import (LIFE_EVENT_TEMPLATES, build_saga,
                                                 SagaCoordinator, spec_from_dict)
from gov_platform.wog_orchestration.consent import ConsentLedger
from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway

CLAIMS = {"sub": "u", "custom:slg_role": "INTAKE_SPECIALIST,RESIDENT_SERVICES_AGENT,ELIGIBILITY_CASEWORKER,PERMIT_TECH,RECORDS_TECH"}
APPROVE = {"approved": True, "reviewer": {"sub": "sup"}}

def _run(event, fail_tool=None):
    led = ConsentLedger()
    for spec in LIFE_EVENT_TEMPLATES[event]:
        led.record("RES-9", f"{event}:{spec.intent}", "AAL2")
    govgw = GovernedToolGateway(default_catalog())
    if fail_tool:
        orig = govgw.invoke
        from gov_platform.wog_orchestration.govern import GovernResult
        govgw.invoke = lambda **kw: (GovernResult(False, "DENY", fail_tool, reason="down")
                                     if kw.get("tool") == fail_tool else orig(**kw))
    saga = build_saga(event, govgw, "RES-9", APPROVE)
    conf = {s.intent: True for s in LIFE_EVENT_TEMPLATES[event]}
    return SagaCoordinator(consent=led).run(saga, CLAIMS, {"resident_ref": "RES-9"}, conf)

def test_all_three_life_events_complete():
    for ev in ("moving", "job_loss", "new_business", "disaster", "bereavement"):
        res = _run(ev)
        assert res.status == "COMPLETED", (ev, [(o.name, o.status, o.reason) for o in res.outcomes])

def test_job_loss_touches_phi_and_fti():
    specs = LIFE_EVENT_TEMPLATES["job_loss"]
    classes = {dc for s in specs for dc in s.data_classes}
    assert {"PHI", "FTI"} <= classes

def test_failure_compensates():
    res = _run("moving", fail_tool="crm311.create_service_request")
    assert res.status == "COMPENSATED"
    # the earlier assemble step had no compensate_tool; 311 failed before commit,
    # so nothing to roll back yet — but the saga must report COMPENSATED cleanly
    assert any(o.status == "FAILED" for o in res.outcomes)

def test_new_business_then_permit_failure_rolls_back_form():
    res = _run("new_business", fail_tool="permitting.create_application")
    assert res.status == "COMPENSATED"

def test_late_failure_rolls_back_completed_compensable_step():
    # fail at book_appt (3rd) so open_311 (2nd, has compensate_tool) rolls back
    res = _run("moving", fail_tool="scheduling.book_appointment")
    assert res.status == "COMPENSATED"
    assert "open_311" in res.compensated_steps

def test_spec_dict_roundtrip():
    s = LIFE_EVENT_TEMPLATES["moving"][1]
    assert spec_from_dict(s.to_dict()) == s

def test_bereavement_touches_records_and_benefits():
    intents = {s.intent for s in LIFE_EVENT_TEMPLATES["bereavement"]}
    assert {"records_request", "benefits"} <= intents

def test_disaster_late_failure_rolls_back_311():
    res = _run("disaster", fail_tool="eligibility.create_application")
    assert res.status == "COMPENSATED"
    assert "report_damage" in res.compensated_steps   # the 311 step (compensable) rolls back
