"""HITL is framework-enforced at the gateway: high-risk tools cannot execute without approval."""
from slg_agent_platform.mcp_gateway import MCPGateway

def test_high_risk_blocks_without_approval():
    gw = MCPGateway(connector_mode="fixture")
    r = gw.invoke(user_claims={"sub": "u", "custom:slg_role": "PERMIT_TECH"},
                  agent_id="03-permitting-licensing", tool="permitting.create_application",
                  args={"type": "Building"})
    assert r.decision == "PENDING_APPROVAL"

def test_high_risk_proceeds_with_approval():
    gw = MCPGateway(connector_mode="fixture")
    r = gw.invoke(user_claims={"sub": "u", "custom:slg_role": "PERMIT_TECH"},
                  agent_id="03-permitting-licensing", tool="permitting.create_application",
                  args={"type": "Building"},
                  approval={"approved": True, "reviewer": {"sub": "lead-1"}})
    assert r.decision == "ALLOW"
