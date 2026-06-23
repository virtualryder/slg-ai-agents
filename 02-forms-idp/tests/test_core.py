import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(_REPO/"platform_core"), str(_REPO), str(_REPO/"02-forms-idp")]
from agent.core import run_until_gate, resume

CLAIMS = {"sub": "staff-1", "custom:slg_role": "INTAKE_SPECIALIST"}
APPROVAL = {"approved": True, "reviewer": {"sub": "sup-1"}}

def test_workflow_produces_grounded_artifact():
    s = run_until_gate({"raw_request": "upload", "acting_user_claims": CLAIMS})
    assert s["artifact"] and s["grounding_report"]["grounded"]
    assert s["_paused_at_gate"] is True

def test_write_requires_human_approval():
    s = run_until_gate({"raw_request": "assemble", "acting_user_claims": CLAIMS})
    final_no = resume(s, approval=None)
    # without approval the write cannot have produced a committed result
    assert final_no.get("write_result") in (None, {})

def test_resume_with_approval_finalizes():
    s = run_until_gate({"raw_request": "assemble", "acting_user_claims": CLAIMS})
    final = resume(s, APPROVAL)
    assert final["case_status"] in ("ASSEMBLED", "PENDING_OFFICIAL", "PENDING_REVIEW", "ESCALATED")
