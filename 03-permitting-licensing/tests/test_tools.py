import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO/"03-permitting-licensing")]
from tools import gateway_tools as gw
CLAIMS={"sub":"staff-1","custom:slg_role":"PERMIT_TECH"}

def test_read_tool_allowed():
    res=gw.call(CLAIMS, "permitting.check_requirements", {'permit_type': 'Building'})
    assert res.allowed

def test_write_tool_requires_approval():
    res=gw.call(CLAIMS, "permitting.create_application", {'type': 'Building'})
    assert res.decision in ("PENDING_APPROVAL","DENY")
