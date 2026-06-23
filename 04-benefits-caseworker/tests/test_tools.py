import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO/"04-benefits-caseworker")]
from tools import gateway_tools as gw

CLAIMS = {"sub": "staff-1", "custom:slg_role": "ELIGIBILITY_CASEWORKER"}

def test_gather_read_allowed():
    res = gw.call(CLAIMS, "eligibility.screen", {})
    assert res.allowed

def test_write_requires_approval():
    res = gw.call(CLAIMS, "eligibility.create_application", {'program': 'SNAP'})
    assert res.decision == "PENDING_APPROVAL"
