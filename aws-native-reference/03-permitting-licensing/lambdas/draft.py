from _shared import core, ok
def handler(event, _ctx=None):
    return ok({**event, "artifact": {"summary": "drafted from approved source"}})
