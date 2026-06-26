"""Tests for cryptographic JWT verification (RS256 against a JWKS)."""
import base64
import json
import time

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.hashes import SHA256

from slg_agent_platform import jwt_verify
from slg_agent_platform.jwt_verify import JWTInvalid

REGION, POOL, AUD = "us-east-1", "us-east-1_Abc123", "client-app-1"
ISSUER = jwt_verify.cognito_issuer(REGION, POOL)
KID = "test-key-1"
_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _b64(d: bytes) -> str:
    return base64.urlsafe_b64encode(d).rstrip(b"=").decode()


def _jwks():
    pn = _KEY.public_key().public_numbers()
    n = pn.n.to_bytes((pn.n.bit_length() + 7) // 8, "big")
    e = pn.e.to_bytes((pn.e.bit_length() + 7) // 8, "big")
    return {"keys": [{"kid": KID, "kty": "RSA", "alg": "RS256", "use": "sig",
                      "n": _b64(n), "e": _b64(e)}]}


def _make_token(claims, *, kid=KID, alg="RS256", sign=True):
    header = {"alg": alg, "kid": kid, "typ": "JWT"}
    h = _b64(json.dumps(header).encode())
    p = _b64(json.dumps(claims).encode())
    signing_input = f"{h}.{p}".encode()
    sig = _KEY.sign(signing_input, padding.PKCS1v15(), SHA256()) if sign else b"x"
    return f"{h}.{p}.{_b64(sig)}"


def _claims(**over):
    now = int(time.time())
    base = {"iss": ISSUER, "aud": AUD, "sub": "user-1", "exp": now + 300,
            "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
    base.update(over)
    return base


def _verify(token):
    return jwt_verify.verify_jwt(token, jwks=_jwks(), issuer=ISSUER, audience=AUD)


def test_valid_token_verifies_and_returns_roles():
    claims = _verify(_make_token(_claims()))
    assert claims["sub"] == "user-1"
    assert jwt_verify.verified_roles(claims) == ["RESIDENT_SERVICES_AGENT"]


def test_tampered_payload_rejected():
    h, p, s = _make_token(_claims()).split(".")
    forged_payload = base64.urlsafe_b64encode(
        json.dumps(_claims(sub="attacker")).encode()).rstrip(b"=").decode()
    with pytest.raises(JWTInvalid):
        _verify(f"{h}.{forged_payload}.{s}")


def test_alg_none_rejected():
    with pytest.raises(JWTInvalid):
        _verify(_make_token(_claims(), alg="none", sign=False))


def test_wrong_issuer_rejected():
    with pytest.raises(JWTInvalid):
        _verify(_make_token(_claims(iss="https://evil.example.com")))


def test_wrong_audience_rejected():
    with pytest.raises(JWTInvalid):
        _verify(_make_token(_claims(aud="some-other-client")))


def test_expired_token_rejected():
    with pytest.raises(JWTInvalid):
        _verify(_make_token(_claims(exp=int(time.time()) - 3600)))


def test_unknown_kid_rejected():
    with pytest.raises(JWTInvalid):
        _verify(_make_token(_claims(), kid="not-in-jwks"))
