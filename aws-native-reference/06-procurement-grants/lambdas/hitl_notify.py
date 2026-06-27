"""
Human gate (waitForTaskToken target) — publish the approval CONTRACT and PARK the pending
approval (with its task token) for the reviewer service. (P7)

The workflow pauses here. This step computes exactly what needs approving (requestor + agent
+ tool + arguments) and, when a PendingApprovals table is configured, writes a PENDING record
keyed by an approval_id together with the Step Functions task token. The authenticated reviewer
service then lists that record and, on approval, mints a *bound* token (separation of duties,
server-side secret) and resumes the execution via SendTaskSuccess. This step does NOT mint the
token (that would defeat SoD). Fail-safe: if the table is not configured (offline/dev), it just
emits the contract and the smoke-test reviewer stand-in mints directly.
"""
import os
import uuid

from _shared import ok
from slg_agent_platform.mcp_gateway import approvals

ACTION_TOOL = {'DRAFT_RFP': 'procurement.draft_rfp'}
AGENT_ID = os.getenv("AGENT_ID", "06-procurement-grants")


def _park(approval_id, task_token, contract):
    """Persist the pending approval (+ task token) so the reviewer service can act on it."""
    table = os.getenv("PENDING_TABLE")
    if not table or not task_token:
        return False
    try:
        from slg_agent_platform.reviewer.store import DynamoDBPendingStore
        DynamoDBPendingStore(table).put({
            "approval_id": approval_id, "task_token": task_token,
            "agent_id": contract["agent_id"], "requestor": contract["requestor"],
            "tool": contract["tool"], "args": contract["args"],
        })
        return True
    except Exception:  # fail safe — the contract is still emitted for the dev stand-in
        return False


def handler(event, _ctx=None):
    # waitForTaskToken delivers {"input": <case>, "token": <task token>}; tolerate a flat event too.
    case = event.get("input", event)
    task_token = event.get("token")
    action = case.get("recommended_action")
    tool = ACTION_TOOL.get(action)
    contract = approval_id = None
    parked = False
    if tool:
        args = {"type": case.get("request_type", "General"),
                "description": case.get("raw_request", "")}
        claims = case.get("acting_user_claims", {})
        contract = {"requestor": claims.get("sub"), "agent_id": AGENT_ID, "tool": tool,
                    "args": args, "args_hash": approvals.args_hash(args)}
        approval_id = str(uuid.uuid4())
        parked = _park(approval_id, task_token, contract)
    return ok({**case, "review_status": "PENDING", "notified": True,
               "approval_contract": contract, "approval_id": approval_id, "parked": parked})
