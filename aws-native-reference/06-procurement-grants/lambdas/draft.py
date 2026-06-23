from _shared import ok
def handler(event,_ctx=None):
    return ok({**event, "artifact": {"summary": "drafted from approved source"}})
