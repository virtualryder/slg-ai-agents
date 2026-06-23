# agent/state.py
# ============================================================
# ResidentServicesState — state object for the Resident Services & 311 workflow.
#
# Context of use: the agent UNDERSTANDS a resident's plain-language request,
# DETERMINES the responsible agency, RETRIEVES authoritative public content,
# DRAFTS a cited answer, and — only for authenticated, consented residents —
# checks case status, creates a 311 service request, or books an appointment.
# It NEVER discloses application/tax/benefit/case data based only on a name and
# address, and every consequential write passes the gateway's human-approval gate.
# ============================================================
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    ANSWER = "ANSWER"                  # clean, grounded public answer -> human gate
    VERIFY_IDENTITY = "VERIFY_IDENTITY"  # personal data requested; require auth first
    CREATE_REQUEST = "CREATE_REQUEST"    # open a 311 service request (high-risk write)
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    REVISE = "REVISE"                  # grounding/accessibility issue: bounded revision
    ESCALATE = "ESCALATE"              # sensitive/complex: route to staff


class ResidentServicesState(TypedDict, total=False):
    # ── Intake ────────────────────────────────────────────────────────────────
    request_id: str
    raw_request: str
    channel: str                 # WEB | CHAT | VOICE
    locale: str                  # e.g. en-US, es-US

    # ── Acting user (gateway adoption) ────────────────────────────────────────
    acting_user_claims: Dict[str, Any]

    # ── Intent + routing ──────────────────────────────────────────────────────
    intent: str                  # service_request | status_lookup | appointment | policy_question | escalate
    responsible_agency: Optional[str]

    # ── Identity / consent ────────────────────────────────────────────────────
    needs_identity: bool
    identity_verified: bool
    resident_ref: Optional[str]

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_sources: List[Dict[str, Any]]

    # ── Draft answer ──────────────────────────────────────────────────────────
    draft_answer: str
    citations: List[Dict[str, str]]
    answer_drafted_by: str       # bedrock | anthropic | demo-stub

    # ── Compliance check ──────────────────────────────────────────────────────
    grounding_report: Dict[str, Any]
    accessibility_report: Dict[str, Any]
    pii_ok: bool
    quality_findings: List[str]

    recommended_action: RecommendedAction

    # ── Disposition ───────────────────────────────────────────────────────────
    service_request_id: Optional[str]
    appointment_id: Optional[str]
    case_status: str             # INTAKE | PENDING_REVIEW | ANSWERED | REQUEST_CREATED | ESCALATED
    revision_count: int

    # ── Infra ─────────────────────────────────────────────────────────────────
    messages: List[Any]
    current_step: str
    completed_steps: List[str]
    errors: List[Dict[str, Any]]

    # ── Audit trail (records retention / public-records posture) ──────────────
    audit_trail: List[Dict[str, Any]]
