import json
from pathlib import Path
def test_asl_waitfortasktoken():
    asl=json.loads((Path(__file__).resolve().parents[1]/"stepfunctions/08_public_safety_health.asl.json").read_text())
    assert "waitForTaskToken" in asl["States"]["HumanGate"]["Resource"]
    assert asl["States"]["Finalize"]["End"] is True
