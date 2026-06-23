from gov_platform.wog_orchestration.consent import ConsentLedger

def test_consent_required_and_recorded():
    led = ConsentLedger()
    assert not led.check("RES-1", "moving:form").allowed
    led.record("RES-1", "moving:form", "AAL2")
    assert led.check("RES-1", "moving:form", required_aal="AAL2").allowed

def test_insufficient_assurance_fails_closed():
    led = ConsentLedger()
    led.record("RES-1", "moving:form", "AAL1")
    d = led.check("RES-1", "moving:form", required_aal="AAL2")
    assert not d.allowed and "assurance" in d.reason
