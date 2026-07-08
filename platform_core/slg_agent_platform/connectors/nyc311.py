"""
NYC 311 Service Requests connector — a REAL external SLG system of record (read-only).

This is the "one real connector per vertical" work for the hero agent
(01-resident-services-311): it replaces the fixture 311/CRM source with the
**NYC 311 Service Requests** dataset on NYC Open Data (Socrata) — a genuine,
public system of record for resident service requests. It proves the governed
pattern (deny-by-default gateway -> scoped token -> PII masking -> human gate ->
append-only audit) against a real API instead of a fixture, and needs **no auth**
because reads are public (an optional app token raises the throttling limit).

  Endpoint : https://data.cityofnewyork.us/resource/erm2-nwe9.json   (public; optional app token)
  Docs     : https://dev.socrata.com/foundry/data.cityofnewyork.us/erm2-nwe9

Design contract (same method names the crm311 fixture exposes, so this is a
drop-in interchangeable connector behind the MCP gateway — see
policy.TOOL_REGISTRY entries "crm311.*"):

  * get_service_request / search_requests / search_duplicates  -> READ real 311
    data (implemented here).
  * create_service_request / update_service_request            -> NOT SUPPORTED.
    NYC 311 Open Data is a READ-ONLY public mirror; opening or mutating a real
    service request writes to the city's own system of record (e.g. Salesforce /
    the 311 platform) and stays **human-gated**. Calling them raises, which is the
    correct, fail-closed behavior and reinforces the governance story: the agent
    can read the real world but cannot write to it.

  * stdlib-only HTTP (urllib), timeouts, fail-closed (any error raises).
  * PII masking still runs downstream on the returned text even though the public
    311 feed is already public — the control is exercised, not assumed.

The regulated variant (the customer's authenticated 311/CRM write API behind an
agency gateway) is a documented follow-on with the same interface; swap the
adapter, keep the agent.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib import request as _urllib_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .base import Connector

_DEFAULT_BASE = "https://data.cityofnewyork.us"
_DATASET = "erm2-nwe9"
_TIMEOUT = 20

# ── Deterministic complaint-category classifier ──────────────────────────────
# Maps a raw 311 complaint_type/descriptor onto a normalized service category.
# This is the 311 analog of Agent 02's deterministic seriousness assessor: a
# non-LLM, unit-testable classification the scored eval measures against gold.
_CATEGORY_KEYWORDS = {
    "Street/Sidewalk": ["pothole", "street condition", "sidewalk", "curb", "street light",
                        "street sign", "sign", "traffic signal"],
    "Sanitation": ["trash", "sanitation", "dirty", "missed collection", "recycling",
                   "litter", "dumping", "sweeping", "garbage"],
    "Noise": ["noise"],
    "Housing": ["heat", "hot water", "plumbing", "paint", "door", "window", "mold",
                "apartment", "unsanitary", "pests", "hpd", "elevator", "ceiling"],
    "Parking/Vehicle": ["illegal parking", "blocked driveway", "abandoned vehicle",
                        "derelict vehicle", "parking"],
    "Water/Sewer": ["water", "sewer", "catch basin", "hydrant", "leak", "flooding"],
    "Parks/Trees": ["tree", "park", "forestry"],
    "Consumer/Business": ["consumer complaint", "business", "vendor", "store"],
}


def classify_category(complaint_type: str = "", descriptor: str = "") -> str:
    """Deterministically classify a 311 request into a normalized service category.

    Keyword match on complaint_type first (most specific), then descriptor.
    Returns 'General' when nothing matches. Order-stable and dependency-free.
    """
    hay = f"{complaint_type or ''} {descriptor or ''}".lower()
    for category, kws in _CATEGORY_KEYWORDS.items():
        if any(k in hay for k in kws):
            return category
    return "General"


def _app_token() -> str:
    """Optional Socrata app token (raises the throttle limit). Env or Secrets Manager."""
    tok = os.getenv("NYC311_APP_TOKEN", "")
    if tok:
        return tok
    try:  # pragma: no cover - depends on customer secrets wiring
        from slg_agent_platform.secrets import get_secret  # type: ignore
        return get_secret("nyc311_app_token", default="") or ""
    except Exception:
        return ""


def _date_only(value: Optional[str]) -> str:
    """Return the YYYY-MM-DD portion of a Socrata floating timestamp (or '')."""
    if not value:
        return ""
    return str(value).split("T", 1)[0]


class NYC311Connector(Connector):
    """Real, read-only NYC 311 Service Requests connector (kind='crm311')."""

    kind = "crm311"
    source = "NYC 311 Service Requests (NYC Open Data, Socrata)"

    def __init__(self, base_url: str = "", app_token: str = "") -> None:
        self._base_url = (base_url or os.getenv("NYC311_BASE_URL", _DEFAULT_BASE)).rstrip("/")
        self._app_token = app_token  # empty -> resolved lazily

    # -- HTTP -----------------------------------------------------------------
    def _get(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """GET the dataset with SoQL params. Fail-closed: any error raises.

        Socrata returns a bare JSON array of records.
        """
        url = f"{self._base_url}/resource/{_DATASET}.json?{urlencode(params)}"
        headers = {"Accept": "application/json"}
        token = self._app_token or _app_token()
        if token:
            headers["X-App-Token"] = token
        req = _urllib_request.Request(url, headers=headers, method="GET")
        try:
            with _urllib_request.urlopen(req, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"NYC 311 API error [{exc.code}] for {url}: {exc}") from exc
        except (URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"NYC 311 API call failed for {url}: {exc}") from exc
        if not isinstance(data, list):
            raise RuntimeError(f"NYC 311 API returned a non-list payload for {url}")
        return data

    # -- Mapping raw 311 record -> suite request record -----------------------
    @staticmethod
    def _map_record(r: Dict[str, Any]) -> Dict[str, Any]:
        complaint_type = r.get("complaint_type", "") or ""
        descriptor = r.get("descriptor", "") or ""
        agency = r.get("agency", "") or ""
        agency_name = r.get("agency_name", "") or agency
        borough = r.get("borough", "") or ""
        address = r.get("incident_address", "") or ""
        status = r.get("status", "") or "Unknown"
        created = _date_only(r.get("created_date"))
        closed = _date_only(r.get("closed_date"))
        category = classify_category(complaint_type, descriptor)

        record = {
            # core keys the crm311 fixture returns (shape-compatible) ----------
            "request_id": r.get("unique_key", "") or "",
            "type": complaint_type,
            "status": status,
            "opened": created,
            "department": agency_name,
            # real 311 fields --------------------------------------------------
            "complaint_type": complaint_type,
            "descriptor": descriptor,
            "category": category,
            "agency": agency,
            "agency_name": agency_name,
            "borough": borough,
            "address": address,
            "created_date": created,
            "closed_date": closed,
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "valid": True,
            "source": NYC311Connector.source,
        }
        record["summary"] = NYC311Connector._compose_summary(record)
        return record

    @staticmethod
    def _compose_summary(rec: Dict[str, Any]) -> str:
        """Compose a factual one-line narrative that claims ONLY what the record
        contains (this is what the grounding eval scores against)."""
        ctype = rec["complaint_type"] or "a service request"
        desc = f" ({rec['descriptor']})" if rec["descriptor"] else ""
        where = f" in {rec['borough']}" if rec["borough"] else ""
        at = f" at {rec['address']}" if rec["address"] else ""
        agency = f"{rec['agency_name']}" + (f" ({rec['agency']})" if rec["agency"] else "")
        opened = f" Opened {rec['created_date']}." if rec["created_date"] else ""
        closed = f" Closed {rec['closed_date']}." if rec["closed_date"] else ""
        return (f"311 service request {rec['request_id']} - {ctype}{desc} reported{where}{at}. "
                f"Handling agency: {agency}. Status: {rec['status']}.{opened}{closed} "
                f"(Source: NYC 311 Open Data, unique_key {rec['request_id']}.)")

    # -- Read interface (crm311.*) --------------------------------------------
    def get_service_request(self, request_id: Optional[str] = None,
                            complaint_type: Optional[str] = None,
                            borough: Optional[str] = None, **_: Any) -> Dict[str, Any]:
        """READ a real 311 request. Priority: explicit unique_key -> by
        complaint_type (most recent) -> most-recent request overall.
        Returns the mapped request record (superset of the crm311 fixture shape).
        """
        params: Dict[str, Any] = {"$limit": 1, "$order": "created_date DESC"}
        clauses = []
        if request_id:
            clauses.append(f"unique_key='{request_id}'")
        if complaint_type:
            clauses.append(f"complaint_type='{complaint_type}'")
        if borough:
            clauses.append(f"borough='{borough.upper()}'")
        if clauses:
            params["$where"] = " AND ".join(clauses)
        rows = self._get(params)
        if not rows:
            return {"request_id": request_id or "", "status": "NOT_FOUND", "valid": False,
                    "source": self.source, "summary": ""}
        return self._map_record(rows[0])

    def search_requests(self, complaint_type: Optional[str] = None,
                        borough: Optional[str] = None, agency: Optional[str] = None,
                        status: Optional[str] = None, limit: int = 5,
                        **_: Any) -> List[Dict[str, Any]]:
        """READ a page of real 311 requests matching optional filters."""
        params: Dict[str, Any] = {"$limit": max(1, min(limit, 50)),
                                  "$order": "created_date DESC"}
        clauses = []
        if complaint_type:
            clauses.append(f"complaint_type='{complaint_type}'")
        if borough:
            clauses.append(f"borough='{borough.upper()}'")
        if agency:
            clauses.append(f"agency='{agency.upper()}'")
        if status:
            clauses.append(f"status='{status}'")
        if clauses:
            params["$where"] = " AND ".join(clauses)
        return [self._map_record(r) for r in self._get(params)]

    def search_duplicates(self, request_id: Optional[str] = None,
                          complaint_type: Optional[str] = None,
                          address: Optional[str] = None,
                          exclude_request_id: Optional[str] = None,
                          limit: int = 5, **_: Any) -> List[Dict[str, Any]]:
        """Find candidate duplicate/related requests by shared complaint_type +
        incident_address. match_score is a transparent heuristic (complaint_type
        match = 0.5, address match = 0.5) — real duplicate detection is a
        customer-validated algorithm; this demonstrates the governed read against
        real data. request_id (the query case) is excluded from results.
        """
        exclude_request_id = exclude_request_id or request_id
        if not complaint_type and not address:
            return []
        params: Dict[str, Any] = {"$limit": max(1, min(limit + 1, 20)),
                                  "$order": "created_date DESC"}
        clauses = []
        if complaint_type:
            clauses.append(f"complaint_type='{complaint_type}'")
        if address:
            clauses.append(f"incident_address='{address}'")
        if clauses:
            params["$where"] = " AND ".join(clauses)
        out: List[Dict[str, Any]] = []
        for r in self._get(params):
            uid = r.get("unique_key", "") or ""
            if exclude_request_id and uid == exclude_request_id:
                continue
            r_ctype = r.get("complaint_type", "") or ""
            r_addr = r.get("incident_address", "") or ""
            score = (0.5 if complaint_type and complaint_type == r_ctype else 0.0) + \
                    (0.5 if address and address == r_addr else 0.0)
            fields = ([f"complaint_type:{complaint_type}"] if complaint_type and complaint_type == r_ctype else []) + \
                     ([f"address:{address}"] if address and address == r_addr else [])
            out.append({"request_id": uid, "match_score": round(score, 2), "fields": fields})
            if len(out) >= limit:
                break
        return out

    # -- Writes are intentionally unsupported (read-only public source) -------
    def create_service_request(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "NYC 311 Open Data is a READ-ONLY public source. Opening a 311 service "
            "request writes to the city's own system of record and remains human-gated. "
            "Use a live agency 311/CRM adapter (CRM311_BASE_URL) or the fixture for write paths."
        )

    def update_service_request(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "NYC 311 Open Data is a READ-ONLY public source. Updating a service request "
            "is a consequential, human-gated action performed against the customer's 311 "
            "platform — never by the agent, never against the public Open Data mirror."
        )
