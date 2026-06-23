# agent/state.py — GovOps IT Service Desk & Modernization
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class RecommendedAction(str, Enum):
    CREATE_TICKET = "CREATE_TICKET"
    RUN_RUNBOOK = "RUN_RUNBOOK"
    ANSWER = "ANSWER"
    ESCALATE = "ESCALATE"
    REVISE = "REVISE"


class AgentState(TypedDict, total=False):
    request_id: str
    raw_request: str
    channel: str
    acting_user_claims: Dict[str, Any]
    intent: str
    needs_identity: bool
    identity_verified: bool
    identity_assertion: str
    gathered: Any
    artifact: Dict[str, Any]
    artifact_text: str
    produced_by: str
    grounding_report: Dict[str, Any]
    accessibility_report: Dict[str, Any]
    pii_ok: bool
    quality_findings: List[str]
    recommended_action: "RecommendedAction"
    write_result: Optional[Dict[str, Any]]
    case_status: str
    revision_count: int
    human_approval: Dict[str, Any]
    current_step: str
    completed_steps: List[str]
    audit_trail: List[Dict[str, Any]]
