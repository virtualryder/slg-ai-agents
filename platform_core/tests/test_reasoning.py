"""Bedrock reasoning helper: deterministic by default, real Bedrock when enabled, fail-safe."""
from slg_agent_platform import reasoning

SOURCES = [{"title": "Report a Problem", "snippet": "Use 311 to report road issues.", "url": "https://city.example.gov/311"}]


def test_deterministic_by_default(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    text, used = reasoning.draft_answer("pothole on Oak St", SOURCES)
    assert used is False and "311" in text


def test_llm_mode_fails_safe_without_creds(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "bedrock")  # no AWS creds in CI -> converse raises -> fallback
    text, used = reasoning.draft_answer("pothole on Oak St", SOURCES)
    assert used is False and text  # fell back, did not raise


def test_llm_mode_success_when_bedrock_available(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "bedrock")

    class _FakeClient:
        def converse(self, **kw):
            assert "messages" in kw and kw["modelId"]
            return {"output": {"message": {"content": [{"text": "Grounded answer from Bedrock."}]}}}

    import boto3
    monkeypatch.setattr(boto3, "client", lambda *a, **k: _FakeClient())
    text, used = reasoning.draft_answer("pothole on Oak St", SOURCES)
    assert used is True and text == "Grounded answer from Bedrock."


def test_guardrail_skipped_without_id(monkeypatch):
    monkeypatch.delenv("BEDROCK_GUARDRAIL_ID", raising=False)
    assert reasoning.guardrail_check("some text")["action"] == "SKIPPED"


def test_guardrail_blocks_when_intervened(monkeypatch):
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-123")

    class _FakeClient:
        def apply_guardrail(self, **kw):
            return {"action": "GUARDRAIL_INTERVENED"}

    import boto3
    monkeypatch.setattr(boto3, "client", lambda *a, **k: _FakeClient())
    res = reasoning.guardrail_check("SSN 123-45-6789")
    assert res["blocked"] is True and res["action"] == "GUARDRAIL_INTERVENED"
