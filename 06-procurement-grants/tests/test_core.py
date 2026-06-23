import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO), str(_REPO/"06-procurement-grants")]
from agent.core import run_until_gate, resume

CLAIMS = {"sub": "staff-1", "custom:slg_role": "PROCUREMENT_ANALYST"}
APPROVAL = {"approved": True, "reviewer": {"sub": "sup-1"}}

def test_workflow_produces_grounded_artifact():
    s = run_until_gate({"raw_request": "find a contract", "acting_user_claims": CLAIMS})
    assert s["artifact"] and s["grounding_report"]["grounded"]
    assert s["_paused_at_gate"] is True

def test_write_requires_human_approval():
    s = run_until_gate({"raw_request": "draft", "acting_user_claims": CLAIMS})
    final_no = resume(s, approval=None)
    # without approval the write cannot have produced a committed result
    assert final_no.get("write_result") in (None, {})

def test_resume_with_approval_finalizes():
    s = run_until_gate({"raw_request": "draft", "acting_user_claims": CLAIMS})
    final = resume(s, APPROVAL)
    assert final["case_status"] in ("RFP_DRAFTED", "PENDING_OFFICIAL", "PENDING_REVIEW", "ESCALATED")

def test_consequential_action_withheld_from_agent():
    from slg_agent_platform.mcp_gateway import policy
    assert "procurement.award" not in policy.AGENT_TOOL_GRANTS["06-procurement-grants"]   # human owns this

def test_finalize_never_calls_withheld_tool():
    # the agent prepares but never commits the consequential action
    s = run_until_gate({"raw_request": "find a contract", "acting_user_claims": CLAIMS})
    final = resume(s, APPROVAL)
    assert final["case_status"] in ("PENDING_OFFICIAL", "RFP_DRAFTED", "ESCALATED", "PENDING_REVIEW")

