import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO/"05-public-records-foia")]
from tools import gateway_tools as gw

CLAIMS = {"sub": "staff-1", "custom:slg_role": "RECORDS_TECH"}

def test_gather_read_allowed():
    res = gw.call(CLAIMS, "records.search", {})
    assert res.allowed

def test_write_requires_approval():
    res = gw.call(CLAIMS, "records.assemble_package", {'record_count': 12})
    assert res.decision == "PENDING_APPROVAL"
