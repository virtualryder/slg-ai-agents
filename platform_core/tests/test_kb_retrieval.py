"""Governed KB/RAG retrieval: the workflow grounds via kb.search_policy THROUGH the gateway,
and live mode is backed by an Amazon Bedrock Knowledge Base."""
import importlib.util
import sys
from pathlib import Path

from slg_agent_platform.connectors.factory import get_connector
from slg_agent_platform.connectors.live import LiveKbConnector

_LAM = Path(__file__).resolve().parents[2] / "aws-native-reference" / "01-resident-services-311" / "lambdas"


def _load_retrieve():
    for m in ("_shared", "core", "retrieve"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(_LAM))
    spec = importlib.util.spec_from_file_location("retrieve_311", _LAM / "retrieve.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_retrieve_runs_through_gateway_and_audits():
    retrieve = _load_retrieve()
    e = {"raw_request": "pothole on Oak St",
         "acting_user_claims": {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}}
    out = retrieve.handler(e)["body"]
    assert out["retrieval_decision"] == "ALLOW"
    assert out["retrieval_audit_id"]
    assert isinstance(out["retrieved_sources"], list) and out["retrieved_sources"]  # kb fixture docs
    assert out["retrieved_sources"][0]["title"]  # mapped source shape


def test_retrieve_denied_for_unentitled_role_keeps_going():
    retrieve = _load_retrieve()
    e = {"raw_request": "x", "retrieved_sources": [{"title": "fallback", "url": "u"}],
         "acting_user_claims": {"sub": "u", "custom:slg_role": "UNRELATED_ROLE"}}
    out = retrieve.handler(e)["body"]
    assert out["retrieval_decision"] == "DENY"
    assert out["retrieved_sources"] == [{"title": "fallback", "url": "u"}]  # fail-safe: kept


def test_live_kb_connector_maps_bedrock_results(monkeypatch):
    class _Fake:
        def retrieve(self, **kw):
            assert kw["knowledgeBaseId"] == "kb-1" and kw["retrievalQuery"]["text"]
            return {"retrievalResults": [
                {"content": {"text": "Trash is collected weekly."},
                 "location": {"s3Location": {"uri": "s3://policies/trash.txt"}},
                 "metadata": {"title": "Trash Schedule", "doc_id": "POL-1"}, "score": 0.91}]}
    import boto3
    monkeypatch.setattr(boto3, "client", lambda *a, **k: _Fake())
    out = LiveKbConnector("kb-1").search_policy(query="trash day")
    assert out[0]["title"] == "Trash Schedule" and out[0]["doc_id"] == "POL-1"
    assert out[0]["snippet"] == "Trash is collected weekly." and out[0]["url"] == "s3://policies/trash.txt"


def test_factory_uses_bedrock_kb_in_live_mode(monkeypatch):
    monkeypatch.setenv("KB_KNOWLEDGE_BASE_ID", "kb-1")
    assert isinstance(get_connector("kb", "live"), LiveKbConnector)


def test_factory_kb_fixture_mode_unaffected():
    conn = get_connector("kb", "fixture")
    assert conn.search_policy(query="anything")  # fixture still returns curated docs
