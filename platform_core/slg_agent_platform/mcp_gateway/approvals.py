"""
Bound, single-use, separation-of-duties human-approval tokens.

The reference gateway previously accepted any object with `approved=true` and a
reviewer `sub`. That is illustrative, not an enforceable control. This module
replaces it with an approval **token bound to the exact transaction** a reviewer
saw, so an approval cannot be reused, retargeted, tampered, or self-issued.

A valid approval token binds, and is verified against, all of:
  * requestor      — the acting user whose request was approved
  * agent_id       — the agent that will execute
  * tool           — the exact tool (no retargeting to a different action)
  * args_hash      — canonical SHA-256 of the arguments (tamper-evident)
  * amount/limit   — optional transaction ceiling (e.g. a payment/refund cap)
  * approver       — the reviewer identity; MUST differ from requestor (SoD)
  * iat / exp      — issued-at / expiry (stale approvals are rejected)
  * jti            — one-time-use nonce (replay is rejected via a nonce store)

In production the signing key is AWS KMS / AgentCore Identity and the nonce store
is DynamoDB with a conditional `PutItem` (exactly-once). Here it is an HMAC + an
in-memory nonce store so the semantics are unit-testable without AWS. Call sites
do not change when the production signer is swapped in.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any, Dict, Optional

_SECRET = os.getenv("APPROVAL_TOKEN_SECRET", secrets.token_hex(32)).encode()
_DEFAULT_TTL = int(os.getenv("APPROVAL_TOKEN_TTL", "900"))  # 15 minutes


class ApprovalInvalid(Exception):
    """Raised when an approval token fails any binding / freshness / SoD / replay check."""


def args_hash(args: Optional[Dict[str, Any]]) -> str:
    body = json.dumps(args or {}, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(body).hexdigest()


def _sign(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = hmac.new(_SECRET, body, hashlib.sha256).hexdigest()
    return f"{body.decode()}.{sig}"


class NonceStore:
    """One-time-use store for approval JTIs. In prod: DynamoDB conditional PutItem."""

    def __init__(self) -> None:
        self._used: set[str] = set()

    def consume(self, jti: str) -> bool:
        """Return True the first time a jti is seen, False on any replay."""
        if jti in self._used:
            return False
        self._used.add(jti)
        return True


def mint_approval_token(
    *,
    requestor: str,
    agent_id: str,
    tool: str,
    args: Optional[Dict[str, Any]] = None,
    approver: str,
    amount_limit: Optional[float] = None,
    ttl_seconds: int = _DEFAULT_TTL,
) -> str:
    """Issued by the human-review service AFTER a reviewer approves THIS request."""
    if approver == requestor:
        # Separation of duties enforced at mint time as well as verify time.
        raise ApprovalInvalid("separation of duties: approver must differ from requestor")
    now = int(time.time())
    payload = {
        "jti": str(uuid.uuid4()),
        "requestor": requestor,
        "agent_id": agent_id,
        "tool": tool,
        "args_hash": args_hash(args),
        "amount_limit": amount_limit,
        "approver": approver,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return _sign(payload)


def verify_approval_token(
    token: str,
    *,
    requestor: str,
    agent_id: str,
    tool: str,
    args: Optional[Dict[str, Any]] = None,
    amount: Optional[float] = None,
    nonce_store: Optional[NonceStore] = None,
    now: Optional[int] = None,
) -> Dict[str, Any]:
    """Verify an approval token is bound to THIS exact request. Raises ApprovalInvalid."""
    now = now or int(time.time())
    try:
        body, sig = token.rsplit(".", 1)
    except (ValueError, AttributeError) as exc:
        raise ApprovalInvalid("malformed approval token") from exc
    expected = hmac.new(_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ApprovalInvalid("bad approval signature")
    claims = json.loads(body)

    if claims.get("exp", 0) < now:
        raise ApprovalInvalid("approval expired")
    if claims.get("requestor") != requestor:
        raise ApprovalInvalid("approval not bound to this requestor")
    if claims.get("agent_id") != agent_id:
        raise ApprovalInvalid("approval not bound to this agent")
    if claims.get("tool") != tool:
        raise ApprovalInvalid("approval not bound to this tool")
    if claims.get("args_hash") != args_hash(args):
        raise ApprovalInvalid("arguments changed after approval")
    if claims.get("approver") == requestor:
        raise ApprovalInvalid("separation of duties: self-approval rejected")
    limit = claims.get("amount_limit")
    if limit is not None and amount is not None and float(amount) > float(limit):
        raise ApprovalInvalid("amount exceeds approved limit")
    if nonce_store is not None and not nonce_store.consume(claims.get("jti", "")):
        raise ApprovalInvalid("approval already used (replay)")
    return claims
