from _shared import ok
# In production this calls Strands/Bedrock with the ANSWER_PROMPT + KB results.
def handler(event, _ctx=None):
    sources = event.get("retrieved_sources", [{"title": "Policy", "snippet": "Answer.", "url": "https://city.example.gov"}])
    return ok({**event, "draft_answer": sources[0]["snippet"],
               "citations": [{"title": s["title"], "url": s["url"]} for s in sources]})
