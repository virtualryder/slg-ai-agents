"""
Retrieve — governed RAG retrieval. (KB/RAG propagation)

Grounds the draft by calling `kb.search_policy` THROUGH the governed gateway: a
policy-checked, scoped-token, audited READ. Fixture mode returns curated policy docs;
live mode (KB_KNOWLEDGE_BASE_ID set) retrieves from an Amazon Bedrock Knowledge Base.
This is the read-path counterpart to the gated write in finalize — the workflow now
touches a system of record on BOTH the read and the write through the same gateway.
Fail-safe: if retrieval is denied/errs, keep any event-supplied sources and continue.
"""
import os

from _shared import ok
from slg_agent_platform.mcp_gateway.runtime import build_gateway

AGENT_ID = os.getenv("AGENT_ID", "05-public-records-foia")


def handler(event, _ctx=None):
    claims = event.get("acting_user_claims", {})
    query = event.get("raw_request", "")
    try:
        gw = build_gateway()
        r = gw.invoke(user_claims=claims, agent_id=AGENT_ID, tool="kb.search_policy",
                      args={"query": query})
        sources = r.result if (r.decision == "ALLOW" and isinstance(r.result, list)) \
            else event.get("retrieved_sources", [])
        return ok({**event, "retrieved_sources": sources,
                   "retrieval_decision": r.decision, "retrieval_audit_id": r.audit_id})
    except Exception as exc:  # fail safe — keep going with whatever sources we have
        return ok({**event, "retrieved_sources": event.get("retrieved_sources", []),
                   "retrieval_decision": "ERROR", "retrieval_error": type(exc).__name__})
