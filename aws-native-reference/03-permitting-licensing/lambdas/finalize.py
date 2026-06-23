from _shared import ok
def handler(event,_ctx=None):
    approved=(event.get("approval") or {}).get("approved")
    return ok({**event, "case_status": ("DONE" if approved else "BLOCKED_NO_APPROVAL")})
