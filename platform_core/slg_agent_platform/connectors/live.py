"""
Live connectors — production adapters behind the SAME method signatures as the
fixtures. A real deployment implements the agency's actual systems here (Accela /
Tyler for permitting, the integrated eligibility system, the ECMS/records system,
ServiceNow for ITSM, the 311/CRM, etc.). Until an adapter is implemented, the
stub raises NotImplementedError so the gap is explicit rather than silent.

A reference HTTP adapter (LiveHttpConnector) is provided to show the pattern:
point <KIND>_BASE_URL at a real service and method calls become REST round-trips
through the gateway's scoped token.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from .base import Connector


class LiveConnector(Connector):
    def __init__(self, kind: str) -> None:
        self.kind = kind

    def __getattr__(self, method: str) -> Any:
        def _call(**kwargs: Any) -> Any:
            raise NotImplementedError(
                f"Live connector for kind={self.kind!r} method={method!r} is not implemented. "
                f"Provide the agency adapter in connectors/live.py or set CONNECTOR_MODE=fixture."
            )
        return _call


class LiveHttpConnector(Connector):
    """Reference REST adapter: <method> -> POST {base_url}/{method} with JSON args."""

    def __init__(self, kind: str, base_url: str, timeout: int = 15) -> None:
        self.kind = kind
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def __getattr__(self, method: str) -> Any:
        def _call(**kwargs: Any) -> Any:  # pragma: no cover - network path
            url = f"{self.base_url}/{method}"
            data = json.dumps(kwargs).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        return _call


class LiveKbConnector(Connector):
    """
    Knowledge-base connector backed by **Amazon Bedrock Knowledge Bases** (managed RAG).

    `search_policy` runs a governed retrieval against the agency's curated KB and maps the
    passages onto the same source shape the fixture returns, so the draft step is unchanged.
    Reached via the gateway like any tool — policy-checked, scoped-token, and audited.
    Configure with KB_KNOWLEDGE_BASE_ID (+ optional KB_MAX_RESULTS, BEDROCK_REGION).
    """
    kind = "kb"

    def __init__(self, knowledge_base_id: str, region: str = None, max_results: int = 5) -> None:
        self.knowledge_base_id = knowledge_base_id
        self.region = region or os.getenv("BEDROCK_REGION", "us-east-1")
        self.max_results = int(os.getenv("KB_MAX_RESULTS", str(max_results)))

    def search_policy(self, **kwargs: Any) -> Any:  # pragma: no cover - network path
        import boto3
        query = kwargs.get("query") or kwargs.get("text") or ""
        client = boto3.client("bedrock-agent-runtime", region_name=self.region)
        resp = client.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": self.max_results}},
        )
        out = []
        for r in resp.get("retrievalResults", []):
            content = (r.get("content") or {}).get("text", "")
            loc = r.get("location") or {}
            uri = ((loc.get("s3Location") or {}).get("uri")
                   or (loc.get("webLocation") or {}).get("url", ""))
            md = r.get("metadata") or {}
            out.append({
                "doc_id": md.get("doc_id") or uri or "kb-doc",
                "title": md.get("title", "Policy document"),
                "snippet": content[:500],
                "url": uri,
                "score": r.get("score"),
            })
        return out

    def get_article(self, **kwargs: Any) -> Any:  # pragma: no cover - network path
        res = self.search_policy(query=kwargs.get("doc_id") or kwargs.get("query", ""))
        return res[0] if res else {"doc_id": kwargs.get("doc_id"), "title": "", "body": "", "url": ""}
