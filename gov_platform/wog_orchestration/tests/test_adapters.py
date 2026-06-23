from gov_platform.wog_orchestration.canonical import (default_registry, DMVAdapter,
    BenefitsAdapter, validate, CANONICAL_SCHEMA_VERSION)

def test_dmv_roundtrip():
    a = DMVAdapter()
    rec = {"customer_no": "55021", "full_name": "Pat Q", "idp_aal": "AAL2",
           "garage_address": {"street": "1 A St", "city": "Town", "st": "NY", "zip": "10001"}}
    res = a.to_canonical(rec)
    assert res.resident_ref == "RES-55021" and validate(res) == []
    back = a.from_canonical(res)
    assert back["customer_no"] == "55021" and back["garage_address"]["st"] == "NY"

def test_benefits_adapter_to_caseref():
    cr = BenefitsAdapter().to_canonical({"case_number": "APP-1", "program_code": "SNAP", "status": "Pending"})
    assert cr.agency == "HHS" and cr.program == "SNAP"

def test_registry_lists_agencies_and_pins_version():
    r = default_registry()
    assert set(r.agencies) == {"DMV", "HHS"}
    assert r.schema_version == CANONICAL_SCHEMA_VERSION
    assert r.adapter("DMV") is not None and r.adapter("Nope") is None
