import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core

def test_classify():
    assert core.classify("report a pothole") == "service_request"
    assert core.classify("status of my case") == "status_lookup"
    assert core.classify("what day is trash") == "policy_question"

def test_status_needs_identity_and_blocks_write():
    assert core.needs_identity("status_lookup")
    assert core.recommended_action("status_lookup", False) == "VERIFY_IDENTITY"

def test_service_request_is_write():
    a = core.recommended_action("service_request", True)
    assert a == "CREATE_REQUEST" and core.is_write_action(a)
