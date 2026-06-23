from gov_platform.wog_orchestration.canonical import Resident, Address, canonical_resident, validate

def test_valid_resident():
    r = canonical_resident("RES-55021", addresses=[Address("1 A St","Town","NY","10001")],
                           assurance_level="AAL2")
    assert validate(r) == []

def test_bad_state_and_token_flagged():
    r = Resident(resident_ref="rawssn", addresses=[Address("1 A St","Town","New York","10001")])
    errs = validate(r)
    assert any("opaque token" in e for e in errs)
    assert any("2-letter" in e for e in errs)
