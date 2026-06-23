from governance.grounding import verify_grounding

def test_grounded_passes():
    state = {"fee": "$75", "department": "Public Works", "eta_days": 5}
    r = verify_grounding("The fee is $75 and Public Works will respond.", state)
    assert r.grounded

def test_fabricated_number_flagged():
    state = {"fee": "$75"}
    r = verify_grounding("The total cost is $4,200 due immediately.", state)
    assert not r.grounded and "$4,200" in r.ungrounded_numbers

def test_fabricated_agency_flagged():
    state = {"department": "Public Works"}
    r = verify_grounding("Contact the Department of Imaginary Affairs today.", state)
    assert not r.grounded
