import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_runner as lr

def test_all_three_execute_through_lambdas():
    for ev in ("moving", "job_loss", "new_business"):
        r = lr.run_execution(ev)
        assert r["status"] == "COMPLETED", (ev, r["outcomes"])
        assert r["evidence"]["event_count"] == len(__import__(
            "gov_platform.wog_orchestration.saga", fromlist=["LIFE_EVENT_TEMPLATES"]
        ).LIFE_EVENT_TEMPLATES[ev])

def test_late_failure_compensates_through_lambdas():
    r = lr.run_execution("moving", fail_tool="scheduling.book_appointment")
    assert r["status"] == "COMPENSATED"
    assert "open_311" in r["rolled_back"]
    assert r["evidence"]["was_compensated"] is True

def test_missing_confirmation_pauses():
    r = lr.run_execution("job_loss", confirmations={})
    assert r["status"] == "PENDING_GATE"

def test_job_loss_evidence_has_phi_and_fti():
    r = lr.run_execution("job_loss")
    assert {"PHI", "FTI"} <= set(r["evidence"]["data_classes"])
