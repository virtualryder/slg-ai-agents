"""
Human gate (waitForTaskToken target) — publish the approval CONTRACT the reviewer must sign. (P5)

A reviewer must mint a *bound* approval token for exactly this requestor + agent + tool + args,
with a different approver (separation of duties), and return it via SendTaskSuccess. This step
does NOT mint the token (that would defeat SoD).
"""
import os

from _shared import ok
from slg_agent_platform.mcp_gateway import approvals

ACTION_TOOL = {'DRAFT_REPORT': 'safety.draft_report'}
AGENT_ID = os.getenv("AGENT_ID", "08-public-safety-health")


def handler(event, _ctx=None):
    action = event.get("recommended_action")
    tool = ACTION_TOOL.get(action)
    contract = None
    if tool:
        args = {"type": event.get("request_type", "General"), "description": event.get("raw_request", "")}
        claims = event.get("acting_user_claims", {})
        contract = {"requestor": claims.get("sub"), "agent_id": AGENT_ID, "tool": tool,
                    "args": args, "args_hash": approvals.args_hash(args)}
    return ok({**event, "review_status": "PENDING", "notified": True, "approval_contract": contract})
