"""Governed connector Lambda — the single backend a gateway target invokes.
The gateway has already authorized (agent grant ∩ user entitlement), minted a
scoped token, and will audit the result. This handler maps {kind, method, args}
onto the agency adapter and returns JSON. In demo it uses the fixture connectors."""
from __future__ import annotations
import json, os, sys

# platform_core is layered into the Lambda (or on PYTHONPATH)
try:
    from slg_agent_platform.connectors import get_connector
except Exception:  # pragma: no cover
    get_connector = None


def handler(event, _ctx=None):
    kind = event["kind"]; method = event["method"]; args = event.get("args", {})
    conn = get_connector(kind, mode=os.getenv("CONNECTOR_MODE", "fixture"))
    result = getattr(conn, method)(**args)
    return {"statusCode": 200, "body": json.dumps(result)}
