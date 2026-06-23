import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO/"06-procurement-grants")]
from tools import gateway_tools as gw
CLAIMS={"sub":"staff-1","custom:slg_role":"PROCUREMENT_ANALYST"}

def test_read_tool_allowed():
    res=gw.call(CLAIMS, "procurement.search_contracts", {})
    assert res.allowed

def test_write_tool_requires_approval():
    res=gw.call(CLAIMS, "procurement.draft_rfp", {})
    assert res.decision in ("PENDING_APPROVAL","DENY")
