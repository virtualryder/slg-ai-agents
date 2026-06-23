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
from .live import LiveConnector, LiveHttpConnector

_KINDS = {"crm311", "kb", "identity", "consent", "scheduling", "gis", "idp",
          "permitting", "eligibility", "records", "procurement", "itsm",
          "safety", "phsurveillance"}


def get_connector(kind: str, mode: Optional[str] = None) -> Connector:
    if kind not in _KINDS:
        raise ValueError(f"unknown connector kind {kind!r}")
    mode = (mode or os.getenv("CONNECTOR_MODE", "fixture")).strip().lower()

    if mode == "live":
        base_url = os.getenv(f"{kind.upper()}_BASE_URL", "")
        if base_url:
            return LiveHttpConnector(kind, base_url=base_url)
        return LiveConnector(kind)

    return build_fixture(kind)
