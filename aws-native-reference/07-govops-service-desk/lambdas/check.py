from _shared import core, ok
def handler(event, _ctx=None):
    action = core.recommended_action(event.get("intent",""))
    return ok({**event, "recommended_action": action, "requires_human_write": core.is_write_action(action)})
