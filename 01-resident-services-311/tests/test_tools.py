import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO / "01-resident-services-311")]

from tools import gateway_tools as gw

CLAIMS = {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}

def test_search_policy_reads():
    assert gw.search_policy(CLAIMS, "trash")

def test_create_request_requires_approval():
    res = gw.create_service_request(CLAIMS, {"type": "Pothole"})
    assert res.decision == "PENDING_APPROVAL"

def test_create_request_with_approval_allows():
    res = gw.create_service_request(CLAIMS, {"type": "Pothole"},
                                    approval={"approved": True, "reviewer": {"sub": "sup-1"}})
    assert res.decision == "ALLOW" and res.result["request_id"]
