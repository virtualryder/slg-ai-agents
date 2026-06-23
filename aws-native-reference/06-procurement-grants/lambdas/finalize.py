from _shared import core, ok
def handler(event, _ctx=None):
    approved = (event.get("approval") or {}).get("approved")
    status = "DONE" if approved else "BLOCKED_NO_APPROVAL"
    return ok({**event, "case_status": status})
