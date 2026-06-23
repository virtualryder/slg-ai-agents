import json
from pathlib import Path

def _asl():
    return json.loads((Path(__file__).resolve().parents[1] / "stepfunctions/lifeevent_saga.asl.json").read_text())

def test_saga_has_compensation_catch():
    asl = _asl()
    runsteps = asl["States"]["RunSteps"]
    assert runsteps["Type"] == "Map" and runsteps["MaxConcurrency"] == 1
    assert any(c["Next"] == "Compensate" for c in runsteps["Catch"])
    assert asl["States"]["Compensate"]["Next"] == "Failed"
    assert asl["States"]["Done"]["Type"] == "Succeed"

def test_iterator_gates_then_writes():
    it = _asl()["States"]["RunSteps"]["Iterator"]["States"]
    assert it["Gate"]["Next"] == "Step" and it["Step"]["End"] is True
