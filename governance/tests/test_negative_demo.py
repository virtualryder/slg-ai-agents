"""CI gate for the SLG Agent 01 (311) 10-point negative demo. Every refusal must fire."""
import importlib.util
import os

import pytest

from slg_agent_platform import budget, jwt_verify
from slg_agent_platform.mcp_gateway import approvals
from slg_agent_platform.mcp_gateway import audit as audit_mod
from slg_agent_platform.mcp_gateway.gateway import MCPGateway
from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-resident-services-311"
USER = {"sub": "u-agent", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
WRONG = {"sub": "u-it", "custom:slg_role": "IT_ANALYST"}
READ = "crm311.get_service_request"
WRITE = "crm311.create_service_request"
ARGS = {"request_id": "SR-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_1_no_jwt():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_2_bad_jwt():
    with pytest.raises(jwt_verify.JWTInvalid):
        jwt_verify.verify_jwt("eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.", jwks={"keys": []},
                              issuer="https://issuer", audience="app")


def test_3_wrong_role():
    assert gw().invoke(user_claims=WRONG, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_4_unregistered_tool():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool="crm311.exfiltrate_all", args={}).decision == "DENY"


def test_5_self_approval():
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-a")


def test_6_replay():
    n = approvals.NonceStore()
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=n)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=n)


def test_7_tampered_args():
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args={"request_id": "X"})


def test_8_masking_fail_closed():
    log = GatewayAuditLog()
    orig = audit_mod.mask
    audit_mod.mask = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("masker down"))
    try:
        with pytest.raises(Exception):
            log.record({"decision": "ALLOW", "tool": READ, "args": {"note": "SSN 123-45-6789"}})
        assert log.records == []
    finally:
        audit_mod.mask = orig


def test_9_audit_fail_closed():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=USER, agent_id=AGENT, tool=READ, args=ARGS)


def test_10_budget_exceeded():
    m = budget.BudgetMeter(agent_id=AGENT, dept="311", monthly_token_cap=1000, cap_behavior="hard")
    m.commit(900)
    assert m.preflight(500).allowed is False


def test_demo_exits_zero():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "01-resident-services-311", "demo", "negative_demo.py")
    spec = importlib.util.spec_from_file_location("slgneg", os.path.abspath(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
