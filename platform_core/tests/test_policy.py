"""Tests for the policy intersection semantics and tool registry integrity."""
from slg_agent_platform.mcp_gateway import policy


def test_every_agent_grant_is_a_real_tool():
    for agent, grants in policy.AGENT_TOOL_GRANTS.items():
        for tool in grants:
            assert tool in policy.TOOL_REGISTRY, (agent, tool)


def test_every_role_entitlement_is_a_real_tool():
    for role, ent in policy.ROLE_ENTITLEMENTS.items():
        for tool in ent:
            assert tool in policy.TOOL_REGISTRY, (role, tool)


def test_high_risk_set_matches_registry():
    expected = {t for t, (_, _, hr) in policy.TOOL_REGISTRY.items() if hr}
    assert policy.HIGH_RISK_TOOLS == expected


def test_intersection_is_minimum_of_grant_and_entitlement():
    d = policy.decide("01-resident-services-311", ["RESIDENT_SERVICES_AGENT"], "scheduling.book_appointment")
    assert d.allowed and d.requires_approval
    d2 = policy.decide("01-resident-services-311", ["PUBLIC_HEALTH_EPIDEMIOLOGIST"], "scheduling.book_appointment")
    assert not d2.allowed


def test_unknown_tool_denied():
    d = policy.decide("01-resident-services-311", ["RESIDENT_SERVICES_AGENT"], "nope.nope")
    assert not d.allowed
