"""
Short-lived, tool-scoped tokens — no standing service accounts.

For every authorized tool call the gateway mints a token scoped to exactly that
tool, carrying the acting government user's context, expiring in seconds. This
mirrors what Amazon Bedrock AgentCore Identity issues (or API Gateway + STS):
ephemeral, least-privilege, attributable.

The token binds the full request context a regulated auditor expects:
  iss/aud, sub, agent_id, tool, scope, agency, env, data_class, req_hash
  (canonical args hash, tamper-evident), jti (one-time-use), iat, exp.

Dev uses a symmetric HMAC (GATEWAY_TOKEN_SECRET or an ephemeral per-process key);
production swaps in AgentCore Identity / STS (asymmetric, KMS-held) without
changing call sites.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional

_SECRET = os.getenv("GATEWAY_TOKEN_SECRET", secrets.token_hex(32)).encode()
_TTL_SECONDS = int(os.getenv("GATEWAY_TOKEN_TTL", "60"))
_ISS = os.getenv("GATEWAY_TOKEN_ISS", "slg-mcp-gateway")
_AUD = os.getenv("GATEWAY_TOKEN_AUD", "slg-connectors")


def request_hash(args: Optional[Dict[str, Any]]) -> str:
    body = json.dumps(args or {}, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(body).hexdigest()


def _sign(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = hmac.new(_SECRET, body, hashlib.sha256).hexdigest()
    return body.decode() + "." + sig


def mint_scoped_token(
    *,
    subject: str,
    agent_id: str,
    tool: str,
    scope: List[str],
    args: Optional[Dict[str, Any]] = None,
    agency: Optional[str] = None,
    env: Optional[str] = None,
    data_class: str = "unspecified",
) -> str:
    now = int(time.time())
    payload = {
        "iss": _ISS,
        "aud": _AUD,
        "jti": str(uuid.uuid4()),
        "sub": subject,
        "agent_id": agent_id,
        "tool": tool,
        "scope": scope,
        "agency": agency or os.getenv("SLG_AGENCY", "unspecified"),
        "env": env or os.getenv("SLG_ENV", "dev"),
        "data_class": data_class,
        "req_hash": request_hash(args),
        "iat": now,
        "exp": now + _TTL_SECONDS,
    }
    return _sign(payload)


class TokenNonceStore:
    """One-time-use store for scoped-token JTIs. In prod: DynamoDB conditional PutItem."""

    def __init__(self) -> None:
        self._used = set()

    def consume(self, jti: str) -> bool:
        if jti in self._used:
            return False
        self._used.add(jti)
        return True


def verify_scoped_token(
    token: str,
    expected_tool: str,
    *,
    expected_args: Optional[Dict[str, Any]] = None,
    audience: Optional[str] = None,
    nonce_store: Optional["TokenNonceStore"] = None,
) -> Dict[str, Any]:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError as exc:
        raise ValueError("malformed token") from exc
    expected_sig = hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("bad token signature")
    claims = json.loads(body)
    if claims.get("exp", 0) < int(time.time()):
        raise ValueError("token expired")
    if claims.get("tool") != expected_tool:
        raise ValueError("token tool scope mismatch")
    if (audience or _AUD) != claims.get("aud"):
        raise ValueError("token audience mismatch")
    if expected_args is not None and claims.get("req_hash") != request_hash(expected_args):
        raise ValueError("token request-hash mismatch (arguments changed)")
    if nonce_store is not None and not nonce_store.consume(claims.get("jti", "")):
        raise ValueError("token already used (replay)")
    return claims
