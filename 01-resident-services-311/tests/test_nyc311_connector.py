"""
Tests for the NYC 311 real 311/CRM connector (the hero-pilot "one real connector").

Two layers:
  * Offline/deterministic (default): monkeypatch the connector's HTTP with recorded
    real-structure cassettes. No network. These are the CI source of truth and cover
    mapping, the governed round-trip (allow reads / gate the write / withhold the
    update), duplicate detection, the deterministic complaint classifier, fail-closed
    writes, and fail-closed PII masking.
  * Opt-in live smoke (RUN_LIVE_NYC311=1): actually calls data.cityofnewyork.us and
    asserts the same governed read against real data. Skipped by default so CI needs
    no network.
"""
import json
import os
import sys
from pathlib import Path

import pytest

AGENT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT))
sys.path.insert(0, str(AGENT.parent / "platform_core"))

from slg_agent_platform.connectors import nyc311  # noqa: E402
from slg_agent_platform.connectors.factory import get_connector  # noqa: E402
from slg_agent_platform.mcp_gateway import MCPGateway  # noqa: E402
from slg_agent_platform.pii import mask  # noqa: E402

_FIX = AGENT / "tests" / "fixtures"
_ONE = json.loads((_FIX / "nyc311_sample.json").read_text(encoding="utf-8"))
_DUPES = json.loads((_FIX / "nyc311_dupes_sample.json").read_text(encoding="utf-8"))

AGENT_ID = "01-resident-services-311"
REP = {"sub": "rep-1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}


@pytest.fixture(autouse=True)
def _governed_mode(monkeypatch):
    monkeypatch.setenv("CONNECTOR_MODE", "live")
    monkeypatch.setenv("CRM311_SOURCE", "nyc311")


def _serve(monkeypatch, payload):
    """Monkeypatch the connector's HTTP layer to return a cassette (offline)."""
    monkeypatch.setattr(nyc311.NYC311Connector, "_get", lambda self, params: payload)


# ── Mapping ──────────────────────────────────────────────────────────────────

def test_maps_real_311_record_to_request_shape():
    rec = nyc311.NYC311Connector._map_record(_ONE[0])
    assert rec["request_id"] == "56789012"
    assert rec["valid"] is True
    assert rec["type"] == "Illegal Parking" and rec["complaint_type"] == "Illegal Parking"
    assert rec["descriptor"] == "Blocked Hydrant"
    assert rec["agency"] == "NYPD"
    assert rec["agency_name"] == "New York City Police Department"
    assert rec["borough"] == "MANHATTAN"
    assert rec["status"] == "Closed"
    assert rec["created_date"] == "2024-03-15" and rec["closed_date"] == "2024-03-18"
    assert rec["category"] == "Parking/Vehicle"
    # summary claims only what the record contains (grounding-friendly)
    assert "56789012" in rec["summary"] and "Illegal Parking" in rec["summary"]


def test_get_service_request_returns_shape(monkeypatch):
    _serve(monkeypatch, _ONE)
    c = nyc311.NYC311Connector()
    rec = c.get_service_request(request_id="56789012")
    assert rec["request_id"] == "56789012" and rec["complaint_type"] == "Illegal Parking"


def test_not_found_shape(monkeypatch):
    _serve(monkeypatch, [])
    rec = nyc311.NYC311Connector().get_service_request(request_id="does-not-exist")
    assert rec["valid"] is False and rec["status"] == "NOT_FOUND"


# ── Deterministic complaint-category classifier ──────────────────────────────

def test_classify_category_deterministic():
    assert nyc311.classify_category("Illegal Parking", "Blocked Hydrant") == "Parking/Vehicle"
    assert nyc311.classify_category("Noise - Residential", "Loud Music/Party") == "Noise"
    assert nyc311.classify_category("HEAT/HOT WATER", "Entire Building") == "Housing"
    assert nyc311.classify_category("Street Condition", "Pothole") == "Street/Sidewalk"
    assert nyc311.classify_category("Something Unmapped", "") == "General"


# ── Duplicate detection (positive match, 2-record cassette) ──────────────────

def test_search_duplicates_positive_match(monkeypatch):
    _serve(monkeypatch, _DUPES)
    c = nyc311.NYC311Connector()
    dups = c.search_duplicates(request_id="70000001",
                               complaint_type="Noise - Residential",
                               address="200 East 10 Street")
    assert len(dups) == 1
    assert dups[0]["request_id"] == "70000002"          # the OTHER request, query case excluded
    assert dups[0]["match_score"] == 1.0                # shared complaint_type (0.5) + address (0.5)


def test_search_duplicates_requires_criteria(monkeypatch):
    _serve(monkeypatch, _DUPES)
    assert nyc311.NYC311Connector().search_duplicates() == []


# ── Writes are fail-closed (read-only public source) ─────────────────────────

def test_create_service_request_raises():
    with pytest.raises(NotImplementedError):
        nyc311.NYC311Connector().create_service_request(type="Pothole")


def test_update_service_request_raises():
    with pytest.raises(NotImplementedError):
        nyc311.NYC311Connector().update_service_request(request_id="X", status="Closed")


# ── Factory routing ──────────────────────────────────────────────────────────

def test_factory_routes_to_nyc311():
    assert type(get_connector("crm311")).__name__ == "NYC311Connector"


def test_factory_default_fixture_not_regressed(monkeypatch):
    # Without the live/source switch, the default path must still be the fixture.
    monkeypatch.delenv("CONNECTOR_MODE", raising=False)
    monkeypatch.delenv("CRM311_SOURCE", raising=False)
    c = get_connector("crm311")
    assert type(c).__name__ == "FixtureBackedConnector"


# ── Governed round-trip through the real gateway ─────────────────────────────

def test_governed_reads_allowed_write_gated_update_withheld(monkeypatch):
    _serve(monkeypatch, _ONE)
    gw = MCPGateway()

    read = gw.invoke(user_claims=REP, agent_id=AGENT_ID,
                     tool="crm311.get_service_request", args={"request_id": "56789012"})
    assert read.allowed and read.decision == "ALLOW"
    assert read.result["request_id"] == "56789012" and read.audit_id
    assert read.scope == ["crm311.get_service_request"]

    dup = gw.invoke(user_claims=REP, agent_id=AGENT_ID, tool="crm311.search_duplicates",
                    args={"complaint_type": "Illegal Parking", "address": "350 5 Avenue"})
    assert dup.allowed

    # create is high-risk -> gated behind a human approval (PENDING_APPROVAL)
    create = gw.invoke(user_claims=REP, agent_id=AGENT_ID,
                       tool="crm311.create_service_request", args={"type": "Pothole"})
    assert not create.allowed and create.requires_approval
    assert create.decision == "PENDING_APPROVAL"

    # update is WITHHELD from the agent entirely (not in its grants) -> DENY
    upd = gw.invoke(user_claims=REP, agent_id=AGENT_ID,
                    tool="crm311.update_service_request",
                    args={"request_id": "56789012", "status": "Closed"})
    assert not upd.allowed and upd.decision == "DENY"


def test_least_privilege_denies_unentitled_role(monkeypatch):
    _serve(monkeypatch, _ONE)
    gw = MCPGateway()
    r = gw.invoke(user_claims={"sub": "x", "custom:slg_role": "PUBLIC_HEALTH_EPIDEMIOLOGIST"},
                  agent_id=AGENT_ID, tool="crm311.get_service_request",
                  args={"request_id": "56789012"})
    assert not r.allowed and r.decision == "DENY"


# ── Fail-closed PII masking on ingested text ─────────────────────────────────

def test_pii_masking_failclosed_on_ingested_text(monkeypatch):
    _serve(monkeypatch, _ONE)
    rec = nyc311.NYC311Connector().get_service_request(request_id="56789012")
    # The public 311 feed is de-identified; stress the control with injected identifiers.
    stressed = rec["summary"] + " reporter jane.doe@example.com SSN 123-45-6789"
    masked = mask(stressed)
    assert "123-45-6789" not in masked
    assert "jane.doe@example.com" not in masked
    # and the real street address in the narrative is masked too
    assert "350 5 Avenue" not in masked


# ── Opt-in live smoke against the real NYC 311 API ───────────────────────────

@pytest.mark.skipif(os.getenv("RUN_LIVE_NYC311", "") not in ("1", "true", "yes"),
                    reason="set RUN_LIVE_NYC311=1 to hit the real data.cityofnewyork.us")
def test_live_nyc311_governed_read():
    gw = MCPGateway()
    r = gw.invoke(user_claims=REP, agent_id=AGENT_ID,
                  tool="crm311.get_service_request", args={})   # most-recent request
    assert r.allowed and r.result.get("valid") is True
    assert r.result.get("request_id")            # a real 311 unique_key
    assert r.audit_id                            # audited
