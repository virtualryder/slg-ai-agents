import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "platform_core"))
from _shared import core, ok
from governance.grounding import verify_grounding  # noqa: E402
def handler(event, _ctx=None):
    rep = verify_grounding(event.get("draft_answer", ""), {"sources": event.get("retrieved_sources", [])})
    action = core.recommended_action(event.get("intent",""), event.get("identity_verified", False))
    return ok({**event, "grounded": rep.grounded, "recommended_action": action,
               "requires_human_write": core.is_write_action(action)})
