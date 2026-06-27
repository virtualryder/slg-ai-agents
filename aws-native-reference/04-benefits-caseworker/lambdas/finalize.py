"""
Finalize — performs the consequential action THROUGH the governed gateway. (P5)

Runs MCPGateway.invoke in-process for a write action: deny-by-default policy + bound,
single-use, separation-of-duties human approval (the token the reviewer supplied at the
waitForTaskToken gate, carried in $.approval) + scoped token + connector + append-only audit.
If the gateway does not ALLOW, nothing is written and the case is BLOCKED — fail closed.
Non-write actions take no tool call.
"""
import os

from _shared import ok
from slg_agent_platform.mcp_gateway.runtime import build_gateway

ACTION_TOOL = {'CREATE_APPLICATION': 'eligibility.create_application', 'DRAFT_NOTICE': 'eligibility.generate_notice'}
AGENT_ID = os.getenv("AGENT_ID", "04-benefits-caseworker")


def handler(event, _ctx=None):
    action = event.get("recommended_action")
    tool = ACTION_TOOL.get(action)
    if not tool:
        return ok({**event, "case_status": "COMPLETED"})

    args = {"type": event.get("request_type", "General"), "description": event.get("raw_request", "")}
    claims = event.get("acting_user_claims", {})
    approval = event.get("approval")  # bound approval token from the reviewer at the gate

    gw = build_gateway()
    r = gw.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args, approval=approval)

    if r.decision == "ALLOW":
        return ok({**event, "case_status": "ACTION_COMPLETED", "tool": tool,
                   "result": r.result, "gateway_decision": r.decision, "audit_id": r.audit_id})
    status = "BLOCKED_NO_APPROVAL" if r.decision == "PENDING_APPROVAL" else "BLOCKED_DENIED"
    return ok({**event, "case_status": status, "tool": tool,
               "gateway_decision": r.decision, "audit_id": r.audit_id, "reason": r.reason})
