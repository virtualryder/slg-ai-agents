import sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "lambdas")]
import _shared, gate, step, compensate
from gov_platform.wog_orchestration.consent import ConsentLedger
from gov_platform.wog_orchestration.events import ComplianceEventBus
from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway
from gov_platform.wog_orchestration.saga import LIFE_EVENT_TEMPLATES

CLAIMS = {"sub": "u", "custom:slg_role": "INTAKE_SPECIALIST"}
APPROVE = {"approved": True, "reviewer": {"sub": "s"}}

def _init():
    c = ConsentLedger(); b = ComplianceEventBus(); g = GovernedToolGateway(default_catalog())
    _shared.init(c, b, g); return c, b, g

def test_gate_blocks_without_consent():
    _init()
    spec = LIFE_EVENT_TEMPLATES["moving"][0].to_dict()
    out = gate.handler({"spec": spec, "event": "moving", "resident_ref": "R1", "confirmations": {}})
    assert out["proceed"] is False

def test_step_commits_and_emits_event():
    c, b, _ = _init()
    spec = LIFE_EVENT_TEMPLATES["moving"][0].to_dict()
    out = step.handler({"spec": spec, "event": "moving", "claims": CLAIMS, "approval": APPROVE,
                        "resident_ref": "R1", "correlation_id": "C1"})
    assert out["status"] == "DONE" and len(b.log) == 1

def test_compensate_rolls_back_compensable():
    c, b, _ = _init()
    committed = [{"name": "open_311", "compensate_tool": "crm311.cancel_service_request"},
                 {"name": "assemble", "compensate_tool": None}]
    out = compensate.handler({"committed": committed, "event": "moving", "resident_ref": "R1", "correlation_id": "C1"})
    assert out["rolled_back"] == ["open_311"]
