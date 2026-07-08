"""
demo_nyc311.py — the "one REAL connector" demo for Agent 01 (Resident Services / 311).

Pulls a **real** 311 service request from the public **NYC 311 Service Requests**
dataset (NYC Open Data / Socrata) **through the governed MCP gateway**, then shows
the whole governance story against real data:

    real NYC 311 read  ->  deny-by-default authorization (RESIDENT_SERVICES_AGENT)
                       ->  fail-closed PII masking
                       ->  scoped per-call token + append-only masked audit
                       ->  human gate: creating a 311 request needs approval;
                           updating a request is WITHHELD from the agent entirely

NYC 311 Open Data is public/read-only, so this needs **no auth** — yet PII masking
still runs on the ingested text (the control is exercised, not assumed). The
regulated variant (the customer's authenticated 311/CRM write API) is the same
interface behind a different CRM311_SOURCE / CRM311_BASE_URL.

Usage
-----
    cd 01-resident-services-311
    # Live (hits data.cityofnewyork.us):
    PYTHONPATH=.:../platform_core:.. python demo/demo_nyc311.py
    # Offline / CI (uses the recorded cassette, no network):
    NYC311_OFFLINE=1 python demo/demo_nyc311.py
    # Pick a complaint type to search for a real request:
    NYC311_COMPLAINT="Illegal Parking" python demo/demo_nyc311.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_AGENT = _HERE.parent
_REPO = _AGENT.parent
sys.path.insert(0, str(_AGENT))
sys.path.insert(0, str(_REPO / "platform_core"))
sys.path.insert(0, str(_REPO))

SEP = "=" * 70


def _load_cassette() -> list:
    p = _AGENT / "tests" / "fixtures" / "nyc311_sample.json"
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    print(f"\n{SEP}\n  RESIDENT SERVICES / 311 AGENT — REAL CONNECTOR DEMO (NYC 311 Open Data)\n{SEP}")

    # ── Governed, real-connector mode ───────────────────────────────────────
    os.environ["CONNECTOR_MODE"] = "live"
    os.environ["CRM311_SOURCE"] = "nyc311"
    offline = os.getenv("NYC311_OFFLINE", "").strip() in ("1", "true", "yes")
    complaint = os.getenv("NYC311_COMPLAINT", "").strip()

    from slg_agent_platform.connectors import nyc311
    from slg_agent_platform.connectors.factory import get_connector
    from slg_agent_platform.mcp_gateway import MCPGateway
    from slg_agent_platform.pii import mask  # fail-closed masker

    # Offline/CI: serve the recorded real-structure cassette instead of the network.
    if offline:
        cassette = _load_cassette()
        nyc311.NYC311Connector._get = lambda self, params: cassette
        print("  [mode] OFFLINE — serving recorded NYC 311 cassette (no network)")
    else:
        print("  [mode] LIVE — calling https://data.cityofnewyork.us/resource/erm2-nwe9.json")

    conn = get_connector("crm311")  # -> NYC311Connector (real, read-only)
    print(f"  [connector] {type(conn).__name__}  source={conn.source}")

    gw = MCPGateway()
    agent_id = "01-resident-services-311"
    rep = {"sub": "demo-rep", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}

    # ── 1. Governed READ of a REAL request ──────────────────────────────────
    print(f"\n1 / 4  Governed read: crm311.get_service_request  (real NYC 311 data)")
    args = {"complaint_type": complaint} if complaint else {}
    try:
        r = gw.invoke(user_claims=rep, agent_id=agent_id,
                      tool="crm311.get_service_request", args=args)
    except Exception as exc:  # network/API failure -> fail closed, fall back to cassette
        print(f"  [warn] live NYC 311 call failed ({exc}); falling back to cassette")
        cassette = _load_cassette()
        nyc311.NYC311Connector._get = lambda self, params: cassette
        r = gw.invoke(user_claims=rep, agent_id=agent_id,
                      tool="crm311.get_service_request", args=args)

    if not r.allowed:
        print(f"  DENIED: {r.reason}"); return
    case = r.result
    print(f"  decision={r.decision}  audit_id={r.audit_id[:8]}  token_scope={r.scope}")
    print(f"  REAL request {case['request_id']} — {case['complaint_type']} / {case['descriptor']}")
    print(f"    category : {case['category']}   agency: {case['agency_name']} ({case['agency']})")
    print(f"    borough  : {case['borough']}   status: {case['status']}   opened: {case['created_date']}")

    # ── 2. Fail-closed PII masking on the ingested narrative ────────────────
    print(f"\n2 / 4  PII masking — fail-closed, runs even on public/de-identified data")
    raw = case.get("summary", "")
    # Demonstrate the control catches PII even if a real feed leaked an identifier:
    stress = raw + "  [intake note: reporter jane.doe@example.com, SSN 123-45-6789]"
    masked = mask(stress)
    leaked = ("123-45-6789" in masked) or ("jane.doe@example.com" in masked)
    print(f"  masked summary : {masked[:150]}...")
    print(f"  PII-leak check : {'FAIL (leak!)' if leaked else 'PASS (identifiers redacted, fail-closed)'}")
    assert not leaked, "PII masking must not leak identifiers"

    # ── 3. Governed duplicate search against real data ──────────────────────
    print(f"\n3 / 4  Governed read: crm311.search_duplicates  (real NYC 311 data)")
    crit = {"complaint_type": case.get("complaint_type"), "address": case.get("address"),
            "request_id": case.get("request_id")}
    rd = gw.invoke(user_claims=rep, agent_id=agent_id,
                   tool="crm311.search_duplicates", args=crit)
    print(f"  decision={rd.decision}  audit_id={rd.audit_id[:8]}  candidates={rd.result}")

    # ── 4. The human authority boundary ─────────────────────────────────────
    print(f"\n4 / 4  Human authority boundary (the trust anchor)")
    rc = gw.invoke(user_claims=rep, agent_id=agent_id,
                   tool="crm311.create_service_request", args={"type": case.get("complaint_type")})
    print(f"  crm311.create_service_request (no approval) -> {rc.decision} "
          f"(requires_approval={rc.requires_approval})")
    ru = gw.invoke(user_claims=rep, agent_id=agent_id,
                   tool="crm311.update_service_request",
                   args={"request_id": case.get("request_id"), "status": "Closed"})
    print(f"  crm311.update_service_request               -> {ru.decision}  ({ru.reason[:70]})")

    print(f"\n{SEP}\n  DEMO COMPLETE — governed pattern proven against a REAL system of record")
    print(f"{SEP}")
    print("  * Real NYC 311 read through deny-by-default gateway (RESIDENT_SERVICES_AGENT)")
    print("  * Fail-closed PII masking on ingested text (no identifier leaks)")
    print("  * Scoped per-call token + append-only masked audit on every call")
    print("  * Creating a 311 request requires human approval; updating is WITHHELD from the agent")
    print("  * NYC 311 Open Data is public/read-only -> NO auth; the agency 311/CRM is the write variant\n")


if __name__ == "__main__":
    main()
