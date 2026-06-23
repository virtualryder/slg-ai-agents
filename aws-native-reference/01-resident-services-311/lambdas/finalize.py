from _shared import ok
def handler(event, _ctx=None):
    action = event.get("recommended_action")
    approved = (event.get("approval") or {}).get("approved")
    status = {"CREATE_REQUEST": "REQUEST_CREATED", "BOOK_APPOINTMENT": "REQUEST_CREATED",
              "ESCALATE": "ESCALATED", "VERIFY_IDENTITY": "PENDING_REVIEW"}.get(action, "ANSWERED")
    if event.get("requires_human_write") and not approved:
        status = "BLOCKED_NO_APPROVAL"
    return ok({**event, "case_status": status})
