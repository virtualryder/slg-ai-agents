"""Draft — grounded answer. (P6)

Generates the resident-facing answer with Amazon Bedrock (Converse + the deployed Guardrail)
when LLM_MODE=bedrock; otherwise assembles a deterministic answer from the retrieved sources.
Either way the answer is constrained to the sources and makes no determination — that stays
with the human gate.
"""
from _shared import ok
from slg_agent_platform.reasoning import draft_answer


def handler(event, _ctx=None):
    sources = event.get("retrieved_sources") or [
        {"title": "Policy", "snippet": "Answer.", "url": "https://city.example.gov"}]
    text, used_llm = draft_answer(event.get("raw_request", ""), sources)
    return ok({**event,
               "draft_answer": text,
               "citations": [{"title": s.get("title"), "url": s.get("url")} for s in sources],
               "draft_via": "bedrock" if used_llm else "deterministic"})
