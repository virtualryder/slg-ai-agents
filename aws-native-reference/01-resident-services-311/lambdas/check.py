"""Check — grounding + the DEPLOYED Bedrock Guardrail on the draft. (P6)

verify_grounding (deterministic) confirms the answer is supported by the retrieved sources;
guardrail_check re-applies the deployed Bedrock Guardrail to the OUTPUT (PII / denied topics /
prompt-attack). If either fails, `grounded` is False so the human reviewer sees it. The
recommended action + write flag are computed from the deterministic core.
"""
import sys
from pathlib import Path

_pp = Path(__file__).resolve().parents
if len(_pp) > 3:  # local/test layout only; in AWS Lambda these come from the shared layer
    sys.path.insert(0, str(_pp[3] / "platform_core"))
from _shared import core, ok
from governance.grounding import verify_grounding  # noqa: E402
from slg_agent_platform.reasoning import guardrail_check  # noqa: E402


def handler(event, _ctx=None):
    draft = event.get("draft_answer", "")
    rep = verify_grounding(draft, {"sources": event.get("retrieved_sources", [])})
    gr = guardrail_check(draft)  # deployed Bedrock Guardrail on the output (skips when offline)
    action = core.recommended_action(event.get("intent", ""), event.get("identity_verified", False))
    return ok({**event,
               "grounded": bool(rep.grounded) and not gr["blocked"],
               "guardrail_action": gr["action"],
               "recommended_action": action,
               "requires_human_write": core.is_write_action(action)})
