"""
Connector factory — resolve a connector by kind and mode.

    get_connector("crm311")               # mode from CONNECTOR_MODE (default fixture)
    get_connector("permitting", "live")   # explicit live

Modes:
    fixture  deterministic offline store (demos, CI, evals)   [default]
    live     production adapters (connectors/live.py)

Live mode resolution: if <KIND>_BASE_URL is set (e.g. PERMITTING_BASE_URL), a
LiveHttpConnector is returned (real REST round-trip). Otherwise a LiveConnector
stub is returned so an unimplemented integration fails loudly, not silently.
"""
from __future__ import annotations

import os
from typing import Optional

from .base import Connector
from .fixtures import build_fixture
from .live import LiveConnector, LiveHttpConnector, LiveKbConnector

_KINDS = {"crm311", "kb", "identity", "consent", "scheduling", "gis", "idp",
          "permitting", "eligibility", "records", "procurement", "itsm",
          "safety", "phsurveillance"}


def get_connector(kind: str, mode: Optional[str] = None) -> Connector:
    if kind not in _KINDS:
        raise ValueError(f"unknown connector kind {kind!r}")
    mode = (mode or os.getenv("CONNECTOR_MODE", "fixture")).strip().lower()

    if mode == "live":
        if kind == "crm311":
            # CRM311_SOURCE=nyc311 -> real, public NYC 311 Service Requests
            # (read-only; create/update writes stay human-gated against the
            # customer's own 311 platform). This is the "one real connector"
            # reference for the hero pilot. Guarded + additive: without the
            # switch, the existing base-url / stub live paths are unchanged.
            if os.getenv("CRM311_SOURCE", "").strip().lower() == "nyc311":
                from .nyc311 import NYC311Connector
                return NYC311Connector()
        if kind == "kb":
            kb_id = os.getenv("KB_KNOWLEDGE_BASE_ID", "")
            if kb_id:
                return LiveKbConnector(kb_id)  # Amazon Bedrock Knowledge Base (RAG)
        base_url = os.getenv(f"{kind.upper()}_BASE_URL", "")
        if base_url:
            return LiveHttpConnector(kind, base_url=base_url)
        return LiveConnector(kind)

    return build_fixture(kind)
