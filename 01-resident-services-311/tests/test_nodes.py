import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO), str(_REPO / "01-resident-services-311")]

from agent.core import run_until_gate, resume
from agent.state import RecommendedAction

CLAIMS = {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
APPROVAL = {"approved": True, "reviewer": {"sub": "sup-1"}}  # auto-minted to a bound token in nodes.finalize

def test_policy_question_is_grounded_and_answered():
    s = run_until_gate({"raw_request": "What is my trash pickup day?", "acting_user_claims": CLAIMS})
    assert s["intent"] == "policy_question"
    assert s["grounding_report"]["grounded"]
    assert s["citations"] and s["citations"][0]["url"]
    final = resume(s, APPROVAL)
    assert final["case_status"] == "ANSWERED"

def test_service_request_routes_to_create_and_needs_gate():
    s = run_until_gate({"raw_request": "Report a pothole please", "acting_user_claims": CLAIMS})
    assert s["intent"] == "service_request"
    assert s["recommended_action"] == RecommendedAction.CREATE_REQUEST
    assert s["_paused_at_gate"] is True
    final = resume(s, APPROVAL)
    assert final["case_status"] == "REQUEST_CREATED" and final["service_request_id"]

def test_status_lookup_requires_identity():
    s = run_until_gate({"raw_request": "What is the status of my permit application?",
                        "acting_user_claims": CLAIMS})
    assert s["needs_identity"] and not s["identity_verified"]
    assert s["recommended_action"] == RecommendedAction.VERIFY_IDENTITY
    final = resume(s, APPROVAL)
    assert final["case_status"] == "PENDING_REVIEW"

def test_finalize_blocked_without_approval():
    s = run_until_gate({"raw_request": "Report a pothole", "acting_user_claims": CLAIMS})
    final = resume(s, approval=None)  # reviewer did not approve
    assert final.get("service_request_id") is None
