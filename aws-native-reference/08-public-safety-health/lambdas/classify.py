from _shared import core, ok
def handler(event,_ctx=None):
    return ok({**event, "intent": core.classify(event.get("raw_request",""))})
