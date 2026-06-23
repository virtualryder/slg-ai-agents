from gov_platform.wog_orchestration.saga import Saga, SagaStep, SagaCoordinator
from gov_platform.wog_orchestration.consent import ConsentLedger

CLAIMS = {"sub": "u", "custom:slg_role": "INTAKE_SPECIALIST"}

def _consent(scopes):
    led = ConsentLedger()
    for sc in scopes:
        led.record("RES-9", sc, "AAL2")
    return led

def test_saga_completes_with_consent_and_confirmation():
    led = _consent(["moving:form", "moving:service_request"])
    co = SagaCoordinator(consent=led)
    saga = Saga("moving", "RES-9", [
        SagaStep("assemble", "form", "Shared Services", lambda c, p: {"form": "ok"}, idempotency_key="k1"),
        SagaStep("open311", "service_request", "311", lambda c, p: {"sr": "SR-1"}, idempotency_key="k2"),
    ])
    res = co.run(saga, CLAIMS, {"resident_ref": "RES-9"},
                 confirmations={"form": True, "service_request": True})
    assert res.status == "COMPLETED"
    assert [o.status for o in res.outcomes] == ["DONE", "DONE"]
    assert len(co.bus.log) == 2

def test_saga_pauses_without_confirmation():
    led = _consent(["moving:form"])
    co = SagaCoordinator(consent=led)
    saga = Saga("moving", "RES-9", [SagaStep("assemble", "form", "SS", lambda c, p: {"ok": 1})])
    res = co.run(saga, CLAIMS, {"resident_ref": "RES-9"}, confirmations={})
    assert res.status == "PENDING_GATE" and res.outcomes[0].status == "NEEDS_CONFIRMATION"

def test_saga_compensates_completed_steps_on_failure():
    led = _consent(["moving:form", "moving:service_request"])
    co = SagaCoordinator(consent=led)
    undone = []
    def boom(c, p): raise RuntimeError("311 down")
    saga = Saga("moving", "RES-9", [
        SagaStep("assemble", "form", "SS", lambda c, p: {"form": "ok"},
                 compensate=lambda c, p: undone.append("form")),
        SagaStep("open311", "service_request", "311", boom),
    ])
    res = co.run(saga, CLAIMS, {"resident_ref": "RES-9"},
                 confirmations={"form": True, "service_request": True})
    assert res.status == "COMPENSATED"
    assert undone == ["form"]                 # the completed step was rolled back
    assert "assemble" in res.compensated_steps
    assert any(e["event_type"].endswith(".compensated") for e in co.bus.log)

def test_idempotent_step_skipped_on_rerun():
    led = _consent(["moving:form"])
    co = SagaCoordinator(consent=led)
    calls = []
    saga = Saga("moving", "RES-9", [
        SagaStep("assemble", "form", "SS", lambda c, p: calls.append(1) or {"ok": 1}, idempotency_key="k1"),
    ])
    co.run(saga, CLAIMS, {"resident_ref": "RES-9"}, confirmations={"form": True})
    res2 = co.run(saga, CLAIMS, {"resident_ref": "RES-9"}, confirmations={"form": True})
    assert len(calls) == 1 and res2.outcomes[0].status == "SKIPPED_IDEMPOTENT"
