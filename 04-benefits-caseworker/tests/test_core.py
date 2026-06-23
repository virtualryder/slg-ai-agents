import sys
from pathlib import Path
_REPO=Path(__file__).resolve().parent.parent.parent
sys.path[:0]=[str(_REPO/"platform_core"),str(_REPO),str(_REPO/"04-benefits-caseworker")]
from agent.core import run_until_gate, resume

CLAIMS={"sub":"staff-1","custom:slg_role":"ELIGIBILITY_CASEWORKER"}
APPROVAL={"approved":True,"reviewer":{"sub":"sup-1"}}

def test_workflow_produces_grounded_artifact():
    s=run_until_gate({"raw_request":"qualify","acting_user_claims":CLAIMS})
    assert s["artifact"] and s["grounding_report"]["grounded"] and s["_paused_at_gate"] is True

def test_read_intent_completes_without_write():
    s=run_until_gate({"raw_request":"qualify","acting_user_claims":CLAIMS})
    assert str(s["recommended_action"]) == "RecommendedAction.PRESCREEN"
    final=resume(s, APPROVAL)
    assert final["case_status"] == "PRESCREENED" and final.get("write_result") is None

def test_write_intent_maps_to_its_action_and_gates():
    s = run_until_gate({"raw_request": "apply", "acting_user_claims": CLAIMS})
    assert str(s["recommended_action"]) == "RecommendedAction.CREATE_APPLICATION"
    assert resume(s, approval=None)["case_status"] == "PENDING_APPROVAL"   # no write without approval
    assert resume(s, APPROVAL)["case_status"] in ("APPLICATION_CREATED", "BLOCKED_NEEDS_APPROVER")


def test_consequential_action_withheld_from_agent():
    from slg_agent_platform.mcp_gateway import policy
    assert "eligibility.adjudicate" not in policy.AGENT_TOOL_GRANTS["04-benefits-caseworker"]

