"""311 Step Functions workflow runs its consequential write THROUGH the gateway.

Simulates the deployed ASL in-process: Classify -> Draft -> Check -> [reviewer mints a
bound approval] -> Finalize. Proves the workflow (not just the HTTP route) enforces
deny-by-default + bound approval and only then creates the 311 request + writes audit.
The `OutputPath: $.body` unwrapping and `ResultPath: $.approval` routing from the ASL are
reproduced by taking ['body'] between steps and placing the approval at event['approval'].
"""
import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

_AGENT = Path(__file__).resolve().parents[2] / "aws-native-reference" / "01-resident-services-311"
_LAMBDAS = str(_AGENT / "lambdas")


def _load_311(name):
    """Load a 311 lambda module by file path, avoiding sys.path _shared conflicts."""
    spec = importlib.util.spec_from_file_location(
        f"_311_{name}", Path(_LAMBDAS) / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The 311 lambdas need _shared (their own) and core on sys.path
sys.path.insert(0, _LAMBDAS)
sys.path.insert(0, str(_AGENT))
# If the wog _shared is cached, swap it out temporarily for 311's
_saved_shared = sys.modules.pop("_shared", None)
_shared_311 = importlib.import_module("_shared")
classify = _load_311("classify")
draft = _load_311("draft")
check = _load_311("check")
finalize = _load_311("finalize")
# Restore the original _shared so wog tests still work
sys.modules.pop("_shared", None)
if _saved_shared is not None:
    sys.modules["_shared"] = _saved_shared
from slg_agent_platform.mcp_gateway import approvals  # noqa: E402

EVENT0 = {
    "raw_request": "There is a pothole on Oak Street, please report it.",
    "retrieved_sources": [{"title": "Report a Problem", "snippet": "Use 311.", "url": "https://city.example.gov/311"}],
    "acting_user_claims": {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"},
    "identity_verified": False,
}
TOOL = "crm311.create_service_request"


def _through_check(event):
    e = classify.handler(event)["body"]
    e = draft.handler(e)["body"]
    e = check.handler(e)["body"]
    return e


def _reviewer_token(event, *, approver="cs-supervisor-1", requestor="rep-1"):
    # the reviewer approves THIS exact request (same args finalize will compute)
    args = {"type": event.get("request_type", "General"), "description": event.get("raw_request", "")}
    return approvals.mint_approval_token(requestor=requestor, agent_id="01-resident-services-311",
                                         tool=TOOL, args=args, approver=approver)


def test_write_executes_through_gateway_with_valid_approval():
    e = _through_check(dict(EVENT0))
    assert e["recommended_action"] == "CREATE_REQUEST" and e["requires_human_write"]
    e["approval"] = {"token": _reviewer_token(e), "reviewer": {"sub": "cs-supervisor-1"}}
    out = finalize.handler(e)["body"]
    assert out["case_status"] == "REQUEST_CREATED"
    assert out["gateway_decision"] == "ALLOW"
    assert out["request_id"] and out["audit_id"]          # the connector actually created it + audited


def test_write_blocked_without_approval():
    e = _through_check(dict(EVENT0))
    out = finalize.handler(e)["body"]                      # no approval supplied
    assert out["case_status"] == "BLOCKED_NO_APPROVAL"
    assert out["gateway_decision"] == "PENDING_APPROVAL"
    assert "request_id" not in out                         # nothing was written


def test_self_approval_is_rejected_at_mint():
    e = _through_check(dict(EVENT0))
    with pytest.raises(approvals.ApprovalInvalid):         # approver must differ from requestor
        _reviewer_token(e, approver="rep-1")


def test_tampered_args_after_approval_block_the_write():
    e = _through_check(dict(EVENT0))
    e["approval"] = {"token": _reviewer_token(e), "reviewer": {"sub": "cs-supervisor-1"}}
    e["raw_request"] = "DIFFERENT request body after approval"   # args changed -> hash mismatch
    out = finalize.handler(e)["body"]
    assert out["case_status"] in ("BLOCKED_NO_APPROVAL", "BLOCKED_DENIED")
    assert "request_id" not in out


def test_non_write_action_takes_no_tool_call():
    e = _through_check({**EVENT0, "raw_request": "What are the city office hours?"})
    out = finalize.handler(e)["body"]
    assert out["case_status"] == "ANSWERED" and "request_id" not in out
