"""
Deterministic fixtures for every SLG system of record.

Each entry maps a connector method to either a static payload or a callable that
shapes a response from the call args. These are synthetic, non-sensitive records
designed to exercise the full agent workflow offline — no real constituent data.
"""
from __future__ import annotations

from typing import Any, Dict

from .base import FixtureBackedConnector

# ── 311 / CRM ────────────────────────────────────────────────────────────────
_CRM311 = {
    "get_service_request": lambda a: {
        "request_id": a.get("request_id", "SR-100245"),
        "type": "Pothole", "status": "In Progress", "opened": "2026-06-10",
        "department": "Public Works", "eta_days": 5,
    },
    "search_requests": lambda a: [
        {"request_id": "SR-100245", "type": "Pothole", "status": "In Progress"},
        {"request_id": "SR-100871", "type": "Missed Trash Pickup", "status": "Closed"},
    ],
    "search_duplicates": lambda a: [
        {"request_id": "SR-100246", "match_score": 1.0,
         "fields": ["complaint_type:Pothole", "address:100 Main St"]},
    ],
    "create_service_request": lambda a: {
        "request_id": "SR-100999", "type": a.get("type", "General"),
        "status": "Open", "department": a.get("department", "311"),
    },
    "update_service_request": lambda a: {"request_id": a.get("request_id"), "status": a.get("status", "Updated")},
}

# ── Knowledge base (approved public content / policy) ────────────────────────
_KB = {
    "search_policy": lambda a: [
        {"doc_id": "POL-TRASH-01", "title": "Residential Trash & Recycling Schedule",
         "snippet": "Trash is collected weekly on your zone day; recycling biweekly.",
         "url": "https://city.example.gov/trash", "effective": "2026-01-01"},
        {"doc_id": "POL-PERMIT-07", "title": "When a Building Permit Is Required",
         "snippet": "A permit is required for structural, electrical, plumbing, and mechanical work.",
         "url": "https://city.example.gov/permits", "effective": "2025-07-01"},
    ],
    "get_article": lambda a: {
        "doc_id": a.get("doc_id", "POL-TRASH-01"),
        "title": "Residential Trash & Recycling Schedule",
        "body": "Set out carts by 7:00 AM on your collection day. Bulk pickup is by appointment.",
        "url": "https://city.example.gov/trash", "effective": "2026-01-01",
    },
}

# ── Identity / consent ───────────────────────────────────────────────────────
_IDENTITY = {
    "verify_resident": lambda a: {
        "verified": bool(a.get("assertion")), "resident_id": "RES-55021",
        "assurance_level": "AAL2" if a.get("assertion") else "NONE",
    },
}
_CONSENT = {
    "check": lambda a: {"resident_id": a.get("resident_id", "RES-55021"),
                         "scope": a.get("scope", "status_lookup"), "granted": True,
                         "expires": "2027-01-01"},
    "record": lambda a: {"consent_id": "CNS-7781", "scope": a.get("scope", "status_lookup"),
                         "granted": True, "recorded": "2026-06-23"},
}

# ── Scheduling ───────────────────────────────────────────────────────────────
_SCHEDULING = {
    "get_availability": lambda a: {"service": a.get("service", "permit_counter"),
                                   "slots": ["2026-06-25T10:00", "2026-06-25T14:30", "2026-06-26T09:15"]},
    "book_appointment": lambda a: {"appointment_id": "APT-3391", "service": a.get("service"),
                                   "slot": a.get("slot", "2026-06-25T10:00"), "status": "Confirmed"},
}

# ── GIS / parcel ─────────────────────────────────────────────────────────────
_GIS = {
    "get_parcel": lambda a: {"parcel_id": a.get("parcel_id", "P-44-1207"),
                             "zoning": "R-5 Residential", "flood_zone": "X",
                             "historic_district": False, "lot_sqft": 6500},
}

# ── Intelligent document processing ──────────────────────────────────────────
_IDP = {
    "extract_document": lambda a: {"doc_type": a.get("doc_type", "income_statement"),
                                   "fields": {"applicant_name": "[provided]", "monthly_income": "[provided]"},
                                   "confidence": 0.91, "low_confidence_fields": []},
    "validate_form": lambda a: {"form_id": a.get("form_id", "HUD-2025"),
                                "complete": False, "missing_fields": ["proof_of_residency"],
                                "format_errors": []},
    "assemble_form": lambda a: {"form_id": a.get("form_id", "HUD-2025"),
                                "rendered": True, "package_uri": "s3://intake/assembled/HUD-2025.pdf"},
}

# ── Permitting / licensing ───────────────────────────────────────────────────
_PERMITTING = {
    "get_permit": lambda a: {"permit_id": a.get("permit_id", "PRM-2026-0481"),
                             "type": "Building", "status": "Under Review",
                             "open_reviews": ["Zoning", "Fire"], "completed_reviews": ["Planning"]},
    "check_requirements": lambda a: {"permit_type": a.get("permit_type", "Building"),
                                     "required": ["Zoning review", "Fire review", "Engineering review",
                                                  "Fee payment", "Inspection scheduling"],
                                     "estimated_cycle_days": 21},
    "create_application": lambda a: {"permit_id": "PRM-2026-0999", "status": "Submitted",
                                     "type": a.get("type", "Building")},
    "route_review": lambda a: {"permit_id": a.get("permit_id"), "routed_to": a.get("reviewers", ["Zoning", "Fire"]),
                               "status": "Routed"},
    "issue_permit": lambda a: {"permit_id": a.get("permit_id"), "status": "Issued",
                               "issued_by": a.get("official", "PERMIT_OFFICIAL"), "issued": "2026-06-23"},
}

# ── Benefits / eligibility (deterministic engine is OUTSIDE the LLM) ──────────
_ELIGIBILITY = {
    "screen": lambda a: {"programs_possibly_eligible": ["SNAP", "Medicaid", "LIHEAP"],
                         "nonbinding": True,
                         "disclaimer": "Prescreen only; not an eligibility determination."},
    "get_case": lambda a: {"case_id": a.get("case_id", "APP-778120"),
                           "program": "SNAP", "status": "Pending Verification",
                           "missing_docs": ["income_statement"]},
    "create_application": lambda a: {"case_id": "APP-779000", "program": a.get("program", "SNAP"),
                                     "status": "Draft"},
    "generate_notice": lambda a: {"notice_id": "NOT-5521", "type": a.get("type", "Request for Information"),
                                  "rendered": True, "requires_human_signoff": True},
    "adjudicate": lambda a: {"case_id": a.get("case_id"), "determination": a.get("determination", "PENDING"),
                             "by": a.get("official"), "deterministic_engine_ref": "RULES-SNAP-v12"},
}

# ── Public records / FOIA ────────────────────────────────────────────────────
_RECORDS = {
    "search": lambda a: [
        {"record_id": "REC-9001", "type": "Deed", "parties": "[party]", "date": "1998-03-12"},
        {"record_id": "REC-9002", "type": "Email", "custodian": "Public Works", "date": "2026-02-01"},
    ],
    "classify": lambda a: {"record_id": a.get("record_id", "REC-9002"),
                           "doc_type": "Email", "responsive": True, "duplicate": False},
    "propose_redaction": lambda a: {"record_id": a.get("record_id", "REC-9002"),
                                    "proposed_redactions": [{"type": "SSN", "page": 1},
                                                            {"type": "PII-Address", "page": 2}],
                                    "exemptions_flagged": ["personal privacy"]},
    "assemble_package": lambda a: {"package_id": "PKG-3120", "record_count": a.get("record_count", 12),
                                   "index_uri": "s3://foia/PKG-3120/index.json", "ready_for_review": True},
    "release": lambda a: {"package_id": a.get("package_id"), "status": "Released",
                          "released_by": a.get("official"), "released": "2026-06-23"},
}

# ── Procurement / contracting / grants ───────────────────────────────────────
_PROCUREMENT = {
    "search_contracts": lambda a: [
        {"vehicle_id": "COOP-IT-2025", "type": "Cooperative", "category": "IT Services"},
        {"vehicle_id": "GRANT-FEMA-BRIC", "type": "Grant", "category": "Resilience"},
    ],
    "draft_rfp": lambda a: {"rfp_id": "RFP-2026-014", "sections_drafted": ["Scope", "Requirements",
                            "Evaluation Criteria", "Required Clauses"], "requires_human_signoff": True},
    "compare_bids": lambda a: {"solicitation": a.get("solicitation", "RFP-2026-014"),
                               "scored_matrix_uri": "s3://procure/RFP-2026-014/scores.csv",
                               "note": "Scores computed by deterministic rubric; award is a human decision."},
    "award": lambda a: {"solicitation": a.get("solicitation"), "awarded_to": a.get("vendor"),
                        "by": a.get("official"), "status": "Awarded"},
}

# ── IT service desk / operations ─────────────────────────────────────────────
_ITSM = {
    "get_ticket": lambda a: {"ticket_id": a.get("ticket_id", "INC-44120"),
                             "summary": "VPN connectivity failure", "priority": "P2", "status": "Open"},
    "create_ticket": lambda a: {"ticket_id": "INC-44200", "summary": a.get("summary", "New issue"),
                                "status": "Open"},
    "run_runbook": lambda a: {"runbook": a.get("runbook", "restart-service"),
                              "status": "Executed", "change_record": "CHG-2210",
                              "approved": True},
}

# ── Public safety / public health ────────────────────────────────────────────
_SAFETY = {
    "summarize_incident": lambda a: {"incident_id": a.get("incident_id", "INC-PS-7781"),
                                     "summary": "Summarized from approved source narrative.",
                                     "missing_required_fields": ["disposition_code"]},
    "draft_report": lambda a: {"report_id": "RPT-3320", "rendered": True,
                               "requires_human_signoff": True,
                               "note": "AI does not establish probable cause or take enforcement action."},
}
_PHSURV = {
    "run_query": lambda a: {"question": a.get("question", "weekly flu cases by county"),
                            "validated_sql": "SELECT county, COUNT(*) FROM surveillance WHERE ...",
                            "rows": [{"county": "Example", "cases": 42}],
                            "note": "SQL validated deterministically before execution."},
}

_TABLES: Dict[str, Dict[str, Any]] = {
    "crm311": _CRM311, "kb": _KB, "identity": _IDENTITY, "consent": _CONSENT,
    "scheduling": _SCHEDULING, "gis": _GIS, "idp": _IDP, "permitting": _PERMITTING,
    "eligibility": _ELIGIBILITY, "records": _RECORDS, "procurement": _PROCUREMENT,
    "itsm": _ITSM, "safety": _SAFETY, "phsurveillance": _PHSURV,
}


def build_fixture(kind: str) -> FixtureBackedConnector:
    if kind not in _TABLES:
        raise ValueError(f"no fixture for connector kind {kind!r}")
    return FixtureBackedConnector(kind, _TABLES[kind])
