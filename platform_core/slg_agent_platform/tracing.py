"""
Lightweight tracing — structured, PII-masked spans for observability.

Emits structured log lines suitable for CloudWatch / AgentCore Observability.
Every value passing through is PII/CJI/FTI-masked so a trace is never a back door
around the audit redaction. Use as a context manager around a node or tool call.
"""
from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator

from slg_agent_platform.pii import mask

logger = logging.getLogger("slg.trace")


def _scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, str):
        return mask(obj)
    return obj


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Dict[str, Any]]:
    start = time.time()
    rec: Dict[str, Any] = {"span": name, "attrs": _scrub(attrs)}
    try:
        yield rec
        rec["status"] = "ok"
    except Exception as exc:  # pragma: no cover
        rec["status"] = "error"
        rec["error"] = type(exc).__name__
        raise
    finally:
        rec["ms"] = round((time.time() - start) * 1000, 2)
        logger.info(json.dumps(rec))
