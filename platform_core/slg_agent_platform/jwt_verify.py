"""
JWT verification — establish identity from a CRYPTOGRAPHICALLY VERIFIED token.

The gateway authorizes against claims; this module is what makes those claims
trustworthy. In production the edge (Cognito / API Gateway JWT authorizer /
AgentCore Identity) verifies the token and forwards only verified claims. This
module is the same check, implemented so it is unit-testable and so any service
that receives a raw bearer token can verify it before trusting a single field:

  * signature — RS256 over header.payload using the issuer's JWKS public key
  * alg       — must be RS256; `none` and HS* are rejected (alg-confusion guard)
  * kid       — must match a key in the JWKS
  * iss       — must equal the expected Cognito issuer
  * aud       — must contain the expected app-client id (or `client_id` for access tokens)
  * exp / nbf — must be unexpired / already valid (with small leeway)

Client-supplied role fields are NEVER trusted until they arrive inside a token
that passes this check. `cognito_issuer()` / `cognito_jwks_url()` build the
endpoints; production fetches and caches the JWKS (it rotates).
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.exceptions import InvalidSignature


class JWTInvalid(Exception):
    """Raised when a token fails signature, issuer, audience, expiry, or algorithm checks."""


def cognito_issuer(region: str, user_pool_id: str) -> str:
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"


def cognito_jwks_url(region: str, user_pool_id: str) -> str:
    return cognito_issuer(region, user_pool_id) + "/.well-known/jwks.json"


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _public_key_from_jwk(jwk: Dict[str, Any]):
    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    return RSAPublicNumbers(e, n).public_key()


def verify_jwt(
    token: str,
    *,
    jwks: Dict[str, Any],
    issuer: str,
    audience: str,
    now: Optional[int] = None,
    leeway: int = 60,
) -> Dict[str, Any]:
    """Verify a Cognito-style RS256 JWT and return its claims. Raises JWTInvalid on any failure."""
    now = now or int(time.time())
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except (ValueError, AttributeError) as exc:
        raise JWTInvalid("malformed token") from exc

    try:
        header = json.loads(_b64url_decode(header_b64))
        claims = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(sig_b64)
    except Exception as exc:  # noqa: BLE001
        raise JWTInvalid("undecodable token segments") from exc

    if header.get("alg") != "RS256":
        raise JWTInvalid(f"unsupported alg {header.get('alg')!r} (RS256 required)")
    kid = header.get("kid")
    if not kid:
        raise JWTInvalid("missing kid")

    jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk is None:
        raise JWTInvalid("no matching JWKS key for kid")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    try:
        _public_key_from_jwk(jwk).verify(signature, signing_input, padding.PKCS1v15(), SHA256())
    except InvalidSignature as exc:
        raise JWTInvalid("bad signature") from exc

    if claims.get("iss") != issuer:
        raise JWTInvalid("issuer mismatch")
    aud = claims.get("aud") or claims.get("client_id")
    auds = aud if isinstance(aud, list) else [aud]
    if audience not in auds:
        raise JWTInvalid("audience mismatch")
    if int(claims.get("exp", 0)) < now - leeway:
        raise JWTInvalid("token expired")
    if int(claims.get("nbf", 0)) > now + leeway:
        raise JWTInvalid("token not yet valid")
    return claims


def verified_roles(claims: Dict[str, Any], role_claim: str = "custom:slg_role") -> List[str]:
    """Roles, taken ONLY from verified-token claims (never from a client-supplied dict)."""
    raw = claims.get(role_claim) or claims.get("cognito:groups") or []
    if isinstance(raw, str):
        return [r.strip() for r in raw.split(",") if r.strip()]
    if isinstance(raw, (list, tuple)):
        return [str(r) for r in raw]
    return []
