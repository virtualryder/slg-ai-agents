"""Tests for the connector framework (fixture/live resolution)."""
import pytest

from slg_agent_platform.connectors import get_connector
from slg_agent_platform.connectors.live import LiveConnector, LiveHttpConnector


def test_fixture_default_returns_payload():
    c = get_connector("crm311")
    assert c.get_service_request(request_id="SR-1")["request_id"]


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        get_connector("nope")


def test_live_without_base_url_is_explicit_stub():
    c = get_connector("permitting", mode="live")
    assert isinstance(c, LiveConnector)
    with pytest.raises(NotImplementedError):
        c.get_permit(permit_id="PRM-1")


def test_live_with_base_url_is_http(monkeypatch):
    monkeypatch.setenv("PERMITTING_BASE_URL", "https://permitting.example.gov")
    c = get_connector("permitting", mode="live")
    assert isinstance(c, LiveHttpConnector)


def test_all_registry_kinds_have_fixtures():
    from slg_agent_platform.mcp_gateway import policy
    kinds = {spec[0] for spec in policy.TOOL_REGISTRY.values()}
    for k in kinds:
        get_connector(k)  # should not raise
