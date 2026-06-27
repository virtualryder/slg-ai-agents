"""Check — grounding + the DEPLOYED Bedrock Guardrail on the drafted output, plus the
deterministic recommended action / write flag. verify_grounding confirms the draft is
supported by the retrieved sources; guardrail_check re-applies the deployed Bedrock
Guardrail to the OUTPUT (PII / denied topics / prompt-attack). If either fails, `grounded`
is False so the human reviewer sees it. (Bedrock+RAG propagation)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "platform_core"))
from _shared import core, ok
from governance.grounding import verify_grounding  # noqa: E402
from slg_agent_platform.reasoning import guardrail_check  # noqa: E402


def handler(event, _ctx=None):
    draft = event.get("draft_answer", "")
    rep = verify_grounding(draft, {"sources": event.get("retrieved_sources", [])})
    gr = guardrail_check(draft)  # deployed Bedrock Guardrail on the output (skips when offline)
    action = core.recommended_action(event.get("intent", ""))
    return ok({**event,
               "grounded": bool(rep.grounded) and not gr["blocked"],
               "guardrail_action": gr["action"],
               "recommended_action": action,
               "requires_human_write": core.is_write_action(action)})
