"""Draft — grounded draft via Amazon Bedrock (Converse + the deployed Guardrail) when
LLM_MODE=bedrock; otherwise a deterministic draft assembled from the retrieved sources.
Either way the drafted artifact is constrained to the sources and makes NO determination —
that stays with the human gate. (Bedrock+RAG propagation)
"""
from _shared import ok
from slg_agent_platform.reasoning import draft_answer


def handler(event, _ctx=None):
    sources = event.get("retrieved_sources") or [
        {"title": "Policy", "snippet": "drafted from approved source", "url": "https://agency.example.gov"}]
    text, used_llm = draft_answer(event.get("raw_request", ""), sources)
    return ok({**event,
               "draft_answer": text,
               "artifact": {"summary": text},
               "citations": [{"title": s.get("title"), "url": s.get("url")} for s in sources],
               "draft_via": "bedrock" if used_llm else "deterministic"})
