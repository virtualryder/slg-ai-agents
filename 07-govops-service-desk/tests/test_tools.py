import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO/"07-govops-service-desk")]
from tools import gateway_tools as gw

CLAIMS = {"sub": "staff-1", "custom:slg_role": "IT_ANALYST"}

def test_gather_read_allowed():
    res = gw.call(CLAIMS, "itsm.get_ticket", {'ticket_id': 'INC-44120'})
    assert res.allowed

def test_write_requires_approval():
    res = gw.call(CLAIMS, "itsm.create_ticket", {'summary': 'Issue'})
    assert res.decision == "PENDING_APPROVAL"
