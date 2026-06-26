"""The DEPLOYED connector Lambda must enforce the governed gateway, not bypass it.

These tests import the actual HTTP tool handler (aws-native-reference/_shared/connector/
handler.py) and prove that the deployed path runs deny-by-default policy, the human-approval
gate, and identity-from-verified-claims-only — the gap a reviewer flagged when the route
pointed straight at the connector.
"""
import json
import sys
from pathlib import Path

import pytest

# the connector Lambda lives outside platform_core; add it to the path like the Lambda layer does
_CONN = Path(__file__).resolve().parents[2] / "aws-native-reference" / "_shared" / "connector"
sys.path.insert(0, str(_CONN))
import handler as connector  # noqa: E402

AGENT = "01-resident-services-311"


def _event(kind, method, *, role=None, sub="user-1", args=None, approval=None, agent_id=AGENT):
    claims = {}
    if sub:
        claims["sub"] = sub
    if role:
        claims["custom:slg_role"] = role
    return {
        "pathParameters": {"kind": kind, "method": method},
        "requestContext": {"authorizer": {"jwt": {"claims": claims}}},
        "body": json.dumps({"args": args or {}, "approval": approval, "agent_id": agent_id}),
    }


def _call(event):
    r = connector.handler(event)
    return r["statusCode"], json.loads(r["body"])


def test_entitled_read_is_allowed():
    status, body = _call(_event("kb", "search_policy", role="RESIDENT_SERVICES_AGENT",
                                args={"query": "trash schedule"}))
    assert status == 200 and body["decision"] == "ALLOW"
    assert body["result"] and body["audit_id"]


def test_agent_overreach_is_denied():
    # resident-services agent is not granted permitting tools -> deny-by-default
    status, body = _call(_event("permitting", "issue_permit", role="PERMIT_OFFICIAL",
                                args={"permit_id": "PRM-1"}))
    assert status == 403 and body["decision"] == "DENY"


def test_high_risk_without_approval_is_pending():
    status, body = _call(_event("crm311", "create_service_request",
                                role="RESIDENT_SERVICES_AGENT", args={"type": "Pothole"}))
    assert status == 202 and body["decision"] == "PENDING_APPROVAL"


def test_identity_taken_only_from_verified_authorizer():
    # No verified claims in the authorizer; a forged role in the BODY must be ignored -> fail closed
    ev = _event("kb", "search_policy", role=None, sub=None)
    ev["body"] = json.dumps({"args": {}, "agent_id": AGENT,
                             "claims": {"sub": "attacker", "custom:slg_role": "BENEFITS_SUPERVISOR"}})
    status, body = _call(ev)
    assert status == 403 and body["decision"] == "DENY"


def test_unknown_tool_is_denied():
    status, body = _call(_event("totally", "made_up_tool", role="RESIDENT_SERVICES_AGENT"))
    assert status == 403 and body["decision"] == "DENY"
