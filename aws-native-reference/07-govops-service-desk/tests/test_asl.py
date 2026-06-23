import json
from pathlib import Path

def test_asl_has_waitfortasktoken():
    asl = json.loads((Path(__file__).resolve().parents[1] / "stepfunctions/07_govops_service_desk.asl.json").read_text())
    assert "waitForTaskToken" in asl["States"]["HumanGate"]["Resource"]
    assert asl["States"]["Finalize"]["End"] is True
