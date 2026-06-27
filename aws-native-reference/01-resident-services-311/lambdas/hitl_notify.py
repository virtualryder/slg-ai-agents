"""
Human gate (waitForTaskToken target) — notify the reviewer and publish the exact
approval CONTRACT they must approve.

The workflow pauses here. A reviewer (the production reviewer service in P7; the
`mint_approval.py` reviewer stand-in for the smoke test) must mint a *bound*
approval token for exactly this requestor + agent + tool + arguments, with a
different approver (separation of duties), and return it via SendTaskSuccess.
finalize then presents that token to the gateway. This step only describes what
needs approving; it does NOT mint the token (that would defeat SoD).
"""
import os

from _shared import ok
from slg_agent_platform.mcp_gateway import approvals

ACTION_TOOL = {
    "CREATE_REQUEST": "crm311.create_service_request",
    "BOOK_APPOINTMENT": "scheduling.book_appointment",
}
AGENT_ID = os.getenv("AGENT_ID", "01-resident-services-311")


def handler(event, _ctx=None):
    action = event.get("recommended_action")
    tool = ACTION_TOOL.get(action)
    contract = None
    if tool:
        args = {"type": event.get("request_type", "General"),
                "description": event.get("raw_request", "")}
        claims = event.get("acting_user_claims", {})
        contract = {
            "requestor": claims.get("sub"),
            "agent_id": AGENT_ID,
            "tool": tool,
            "args": args,
            "args_hash": approvals.args_hash(args),
        }
    return ok({**event, "review_status": "PENDING", "notified": True, "approval_contract": contract})
