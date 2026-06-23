import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO/"07-govops-service-desk")]
from tools import gateway_tools as gw
CLAIMS={"sub":"staff-1","custom:slg_role":"IT_ANALYST"}

def test_read_tool_allowed():
    res=gw.call(CLAIMS, "kb.search_policy", {'query': 'it support'})
    assert res.allowed

def test_write_tool_requires_approval():
    res=gw.call(CLAIMS, "itsm.create_ticket", {'summary': 'Reported incident'})
    assert res.decision in ("PENDING_APPROVAL","DENY")
