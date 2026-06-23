import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO),str(_REPO/"08-public-safety-health")]
from agent.core import run_until_gate, resume

CLAIMS={"sub":"staff-1","custom:slg_role":"PUBLIC_SAFETY_ANALYST"}
APPROVAL={"approved":True,"reviewer":{"sub":"sup-1"}}

def test_workflow_produces_grounded_artifact():
    s=run_until_gate({"raw_request":"summarize","acting_user_claims":CLAIMS})
    assert s["artifact"] and s["grounding_report"]["grounded"] and s["_paused_at_gate"] is True

def test_read_intent_completes_without_write():
    s=run_until_gate({"raw_request":"summarize","acting_user_claims":CLAIMS})
    assert str(s["recommended_action"]) == "RecommendedAction.SUMMARIZE"
    final=resume(s, APPROVAL)
    assert final["case_status"] == "SUMMARIZED" and final.get("write_result") is None

def test_write_intent_maps_to_its_action_and_gates():
    s = run_until_gate({"raw_request": "report", "acting_user_claims": CLAIMS})
    assert str(s["recommended_action"]) == "RecommendedAction.DRAFT_REPORT"
    assert resume(s, approval=None)["case_status"] == "PENDING_APPROVAL"   # no write without approval
    assert resume(s, APPROVAL)["case_status"] in ("REPORT_DRAFTED", "BLOCKED_NEEDS_APPROVER")

