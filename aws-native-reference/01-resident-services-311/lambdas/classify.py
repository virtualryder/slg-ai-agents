from _shared import core, ok
def handler(event, _ctx=None):
    intent = core.classify(event.get("raw_request", ""))
    return ok({**event, "intent": intent, "needs_identity": core.needs_identity(intent)})
