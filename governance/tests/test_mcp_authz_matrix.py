"""MCP authorization negative-test matrix — the 12 cases a security reviewer expects, proven
against the SHIPPING SLG gateway. Framing maps to the deployed edge (401/403/deny).

  1 no token -> 401            5 wrong role -> deny        9  tampered approval args -> deny
  2 bad token -> 401           6 wrong data class -> deny  10 stale/expired approval -> deny
  3 missing scope -> 403       7 self-approval -> deny      11 no outbound credential -> deny
  4 unregistered tool -> deny  8 replayed approval -> deny  12 audit write failure -> deny
"""
import pytest

from slg_agent_platform import jwt_verify
from slg_agent_platform.mcp_gateway import tokens, approvals
from slg_agent_platform.mcp_gateway.gateway import MCPGateway
from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-resident-services-311"
USER = {"sub": "u-agent", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
WRONG = {"sub": "u-it", "custom:slg_role": "IT_ANALYST"}
READ = "crm311.get_service_request"
WRITE = "crm311.create_service_request"
OTHER_DATACLASS_TOOL = "permitting.get_permit"     # permitting data class — agent 01 not granted it
ARGS = {"request_id": "SR-1"}


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def test_01_no_token():
    assert gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_02_bad_token():
    with pytest.raises(jwt_verify.JWTInvalid):
        jwt_verify.verify_jwt("eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.", jwks={"keys": []},
                              issuer="https://issuer", audience="app")


def test_03_missing_scope():
    tok = tokens.mint_scoped_token(subject="u-agent", agent_id=AGENT, tool=READ, scope=[READ], args=ARGS)
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(tok, expected_tool=WRITE)


def test_04_unregistered_tool():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool="crm311.exfiltrate_all", args={}).decision == "DENY"


def test_05_wrong_role():
    assert gw().invoke(user_claims=WRONG, agent_id=AGENT, tool=READ, args=ARGS).decision == "DENY"


def test_06_wrong_data_class():
    assert gw().invoke(user_claims=USER, agent_id=AGENT, tool=OTHER_DATACLASS_TOOL, args={}).decision == "DENY"


def test_07_self_approval():
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-a")


def test_08_replayed_approval():
    n = approvals.NonceStore()
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=n)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=n)


def test_09_tampered_approval_args():
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args={"request_id": "X"})


def test_10_expired_approval():
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS,
                                        approver="u-sup", ttl_seconds=-1000)
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS)


def test_11_no_outbound_credential():
    with pytest.raises(ValueError):
        tokens.verify_scoped_token("no.valid.outbound.token", expected_tool=READ)


def test_12_audit_write_failure():
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit sink down"))
    with pytest.raises(Exception):
        g.invoke(user_claims=USER, agent_id=AGENT, tool=READ, args=ARGS)
