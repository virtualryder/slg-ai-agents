from _shared import ok
def handler(event,_ctx=None):
    return ok({**event, "review_status": "PENDING"})
