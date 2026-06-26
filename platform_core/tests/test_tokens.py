"""Tests for hardened scoped tokens (iss/aud/req-hash/expiry/single-use)."""
import pytest

from slg_agent_platform.mcp_gateway import tokens


def _mint(args=None, tool="crm311.create_service_request"):
    return tokens.mint_scoped_token(subject="user-1", agent_id="01", tool=tool,
                                    scope=[tool], args=args, data_class="PII")


def test_token_round_trips_with_full_context():
    args = {"type": "Pothole"}
    claims = tokens.verify_scoped_token(_mint(args), "crm311.create_service_request",
                                        expected_args=args)
    assert claims["iss"] == "slg-mcp-gateway" and claims["aud"] == "slg-connectors"
    assert claims["data_class"] == "PII" and claims["sub"] == "user-1"


def test_tool_scope_mismatch_rejected():
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(_mint(), "crm311.update_service_request")


def test_request_hash_tamper_rejected():
    tok = _mint({"type": "Pothole"})
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(tok, "crm311.create_service_request",
                                   expected_args={"type": "Graffiti"})


def test_audience_mismatch_rejected():
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(_mint(), "crm311.create_service_request", audience="wrong-aud")


def test_single_use_replay_rejected():
    store = tokens.TokenNonceStore()
    tok = _mint({"x": 1})
    tokens.verify_scoped_token(tok, "crm311.create_service_request",
                               expected_args={"x": 1}, nonce_store=store)
    with pytest.raises(ValueError):
        tokens.verify_scoped_token(tok, "crm311.create_service_request",
                                   expected_args={"x": 1}, nonce_store=store)
