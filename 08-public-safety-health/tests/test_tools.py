import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO/"08-public-safety-health")]
from tools import gateway_tools as gw
CLAIMS={"sub":"staff-1","custom:slg_role":"PUBLIC_SAFETY_ANALYST"}

def test_read_tool_allowed():
    res=gw.call(CLAIMS, "safety.summarize_incident", {'incident_id': 'INC-PS-7781'})
    assert res.allowed

def test_write_tool_requires_approval():
    res=gw.call(CLAIMS, "safety.draft_report", {})
    assert res.decision in ("PENDING_APPROVAL","DENY")
