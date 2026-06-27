"""
Finalize — performs the consequential action THROUGH the governed gateway.

This is where the Step Functions workflow actually touches a system of record. It
does NOT call a connector directly. For a write action it runs MCPGateway.invoke
in-process, so the deployed workflow enforces the same controls as the HTTP path:

  policy (agent grant ∩ user entitlement)
   -> bound, single-use, separation-of-duties human approval (the token the
      reviewer supplied at the waitForTaskToken gate, carried in $.approval)
   -> scoped, request-bound, single-use token
   -> connector (fixture | live) creates the 311 service request
   -> append-only audit (DynamoDB conditional PutItem when AUDIT_TABLE is set)

If the gateway does not ALLOW (no/forged/expired approval, not entitled, unknown
tool), NO system-of-record write happens and the case is BLOCKED — fail closed.
Read/answer/escalate actions take no tool call.
"""
import os

from _shared import ok
from slg_agent_platform.mcp_gateway.runtime import build_gateway

# 311 consequential (write) actions -> the governed tool that performs them
ACTION_TOOL = {
    "CREATE_REQUEST": "crm311.create_service_request",
    "BOOK_APPOINTMENT": "scheduling.book_appointment",
}
AGENT_ID = os.getenv("AGENT_ID", "01-resident-services-311")


def handler(event, _ctx=None):
    action = event.get("recommended_action")
    tool = ACTION_TOOL.get(action)

    # Non-write actions: no system-of-record touch.
    if not tool:
        status = {"ESCALATE": "ESCALATED", "VERIFY_IDENTITY": "PENDING_REVIEW"}.get(action, "ANSWERED")
        return ok({**event, "case_status": status})

    # Write action -> through the governed gateway.
    args = {"type": event.get("request_type", "General"),
            "description": event.get("raw_request", "")}
    claims = event.get("acting_user_claims", {})
    approval = event.get("approval")  # bound approval token the reviewer supplied at the gate

    gw = build_gateway()
    result = gw.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args, approval=approval)

    if result.decision == "ALLOW":
        body = result.result or {}
        return ok({**event,
                   "case_status": "REQUEST_CREATED",
                   "request_id": body.get("request_id"),
                   "gateway_decision": result.decision,
                   "audit_id": result.audit_id})

    # DENY / PENDING_APPROVAL / ERROR -> nothing was written; fail closed.
    status = "BLOCKED_NO_APPROVAL" if result.decision == "PENDING_APPROVAL" else "BLOCKED_DENIED"
    return ok({**event,
               "case_status": status,
               "gateway_decision": result.decision,
               "audit_id": result.audit_id,
               "reason": result.reason})
