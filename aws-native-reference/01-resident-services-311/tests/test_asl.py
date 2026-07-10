import json
from pathlib import Path

def test_asl_has_waitfortasktoken_human_gate():
    asl = json.loads((Path(__file__).resolve().parents[1] / "stepfunctions/resident_services.asl.json").read_text())
    hg = asl["States"]["HumanGate"]
    assert "waitForTaskToken" in hg["Resource"]
    assert asl["States"]["Finalize"]["End"] is True

def test_every_state_reachable():
    asl = json.loads((Path(__file__).resolve().parents[1] / "stepfunctions/resident_services.asl.json").read_text())
    assert asl["StartAt"] == "Classify"
    # PipelineFailed is the terminal Fail state that every Task's Catch routes to
    # (added with the Retry/Catch resilience hardening).
    assert set(asl["States"]) == {"Classify","Retrieve","Draft","Check","HumanGate","Finalize","PipelineFailed"}
