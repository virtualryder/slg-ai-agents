from _shared import core, ok
def handler(event, _ctx=None):
    return ok({**event, "review_status": "PENDING"})
