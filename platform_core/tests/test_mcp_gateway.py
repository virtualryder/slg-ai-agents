"""Tests for the deny-by-default MCP authorization gateway (least-privilege intersection)."""
import pytest

from slg_agent_platform.mcp_gateway import MCPGateway, policy
from slg_agent_platform.mcp_gateway.errors import ApprovalRequired, PolicyDenied

AGENT = "01-resident-services-311"
RS_AGENT_CLAIMS = {"sub": "user-rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}


def gw():
    return MCPGateway(connector_mode="fixture")


def test_read_allowed_for_granted_and_entitled():
    r = gw().invoke(user_claims=RS_AGENT_CLAIMS, agent_id=AGENT, tool="kb.search_policy",
                    args={"query": "trash schedule"})
    assert r.decision == "ALLOW" and r.allowed
    assert isinstance(r.result, list) and r.result


def test_fail_closed_without_subject():
    r = gw().invoke(user_claims={"custom:slg_role": "RESIDENT_SERVICES_AGENT"},
                    agent_id=AGENT, tool="kb.search_policy")
    assert r.decision == "DENY" and not r.allowed


def test_agent_overreach_denied():
    # The resident-services agent is not granted permitting tools, even if the user is a PERMIT_OFFICIAL.
    claims = {"sub": "u2", "custom:slg_role": "PERMIT_OFFICIAL"}
    r = gw().invoke(user_claims=claims, agent_id=AGENT, tool="permitting.issue_permit",
                    args={"permit_id": "PRM-1"})
    assert r.decision == "DENY"
    assert "not granted" in r.reason


def test_agent_never_exceeds_user_entitlement():
    # A resident-services agent CAN create a 311 request, but only if the acting user is entitled.
    weak_user = {"sub": "u3", "custom:slg_role": "PUBLIC_HEALTH_EPIDEMIOLOGIST"}
    r = gw().invoke(user_claims=weak_user, agent_id=AGENT, tool="crm311.create_service_request",
                    args={"type": "Pothole"})
    assert r.decision == "DENY"
    assert "not entitled" in r.reason


def test_high_risk_requires_human_approval():
    r = gw().invoke(user_claims=RS_AGENT_CLAIMS, agent_id=AGENT,
                    tool="crm311.create_service_request", args={"type": "Pothole"})
    assert r.decision == "PENDING_APPROVAL" and r.requires_approval


def test_high_risk_proceeds_with_valid_approval():
    approval = {"approved": True, "reviewer": {"sub": "supervisor-1"}}
    r = gw().invoke(user_claims=RS_AGENT_CLAIMS, agent_id=AGENT,
                    tool="crm311.create_service_request", args={"type": "Pothole"},
                    approval=approval)
    assert r.decision == "ALLOW" and r.allowed
    assert r.result["request_id"]


def test_invalid_approval_still_blocks():
    bad = {"approved": True, "reviewer": {}}  # no reviewer identity bound
    r = gw().invoke(user_claims=RS_AGENT_CLAIMS, agent_id=AGENT,
                    tool="crm311.create_service_request", args={"type": "Pothole"}, approval=bad)
    assert r.decision == "PENDING_APPROVAL"


def test_raise_on_deny():
    with pytest.raises(PolicyDenied):
        gw().invoke(user_claims={"custom:slg_role": "X"}, agent_id=AGENT,
                    tool="kb.search_policy", raise_on_deny=True)


def test_consequential_actions_withheld_from_agents():
    # The legally consequential commit actions must NOT be in any agent's grants.
    withheld = {
        "03-permitting-licensing": "permitting.issue_permit",
        "04-benefits-caseworker": "eligibility.adjudicate",
        "05-public-records-foia": "records.release",
        "06-procurement-grants": "procurement.award",
    }
    for agent_id, tool in withheld.items():
        assert tool not in policy.AGENT_TOOL_GRANTS[agent_id], (agent_id, tool)


def test_audit_trail_records_every_attempt():
    g = gw()
    g.invoke(user_claims=RS_AGENT_CLAIMS, agent_id=AGENT, tool="kb.search_policy")
    g.invoke(user_claims={"custom:slg_role": "X"}, agent_id=AGENT, tool="kb.search_policy")
    decisions = [r["decision"] for r in g.audit.records]
    assert "ALLOW" in decisions and "DENY" in decisions
    assert all("audit_id" in r and "ts" in r for r in g.audit.records)
