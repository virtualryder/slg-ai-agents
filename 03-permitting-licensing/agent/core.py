# agent/core.py — Permitting & Licensing
# Framework-free workflow (runs in EXTRACT_MODE=demo with no LLM). graph.py wires
# these same node functions into a LangGraph StateGraph with a HITL interrupt.
from __future__ import annotations
import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from slg_agent_platform.pii import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction

INTENTS = {'requirements': ['what do i need', 'requirement', 'required', 'do i need a permit'], 'status': ['status', 'where is my permit', 'holding'], 'apply': ['apply', 'application', 'submit', 'start a permit'], 'route': ['route', 'review', 'send to']}
PERSONAL_INTENTS = set(['status'])
DEFAULT_INTENT = 'requirements'
GATHER_TOOL = 'permitting.check_requirements'
GATHER_ARGS = {'permit_type': 'Building'}
WRITE_TOOL = 'permitting.create_application'
WRITE_ARGS = {'type': 'Building'}
WRITE_ACTION = 'CREATE_APPLICATION'
DONE_STATUS = 'APPLICATION_CREATED'
WITHHELD_TOOL = 'permitting.issue_permit'   # legally consequential action the agent may NOT call


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"current_step": "intake", "case_status": "INTAKE",
            "revision_count": state.get("revision_count", 0),
            "completed_steps": state.get("completed_steps", []) + ["intake"]}


def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    text = (state.get("raw_request") or "").lower()
    intent = DEFAULT_INTENT
    for cand, kws in INTENTS.items():
        if any(k in text for k in kws):
            intent = cand
            break
    return {"intent": intent, "needs_identity": intent in PERSONAL_INTENTS,
            "current_step": "classify_intent",
            "completed_steps": state.get("completed_steps", []) + ["classify_intent"]}


def check_identity(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("needs_identity"):
        return {"identity_verified": True, "current_step": "check_identity",
                "completed_steps": state.get("completed_steps", []) + ["check_identity"]}
    claims = state.get("acting_user_claims", {})
    res = gw.call(claims, "identity.verify_resident", {"assertion": state.get("identity_assertion", "")}) \
        if state.get("identity_assertion") else None
    verified = bool(res and res.allowed and res.result.get("verified"))
    return {"identity_verified": verified, "current_step": "check_identity",
            "completed_steps": state.get("completed_steps", []) + ["check_identity"]}


def gather(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    res = gw.call(claims, GATHER_TOOL, dict(GATHER_ARGS))
    return {"gathered": (res.result if res and res.allowed else None),
            "current_step": "gather",
            "completed_steps": state.get("completed_steps", []) + ["gather"]}


def produce(state: Dict[str, Any]) -> Dict[str, Any]:
    gathered = state.get("gathered")
    # Demo: deterministic artifact strictly from gathered data (no fabrication).
    artifact = {"summary": "permit application package prepared from approved source data.",
                "source": gathered, "withheld_action": WITHHELD_TOOL}
    text = artifact["summary"]
    return {"artifact": artifact, "artifact_text": text, "produced_by": "demo-stub",
            "current_step": "produce",
            "completed_steps": state.get("completed_steps", []) + ["produce"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("artifact_text", "")
    grounding = verify_grounding(text, {"src": state.get("gathered")})
    access = check_plain_language(text)
    pii_ok = mask(text) == text
    findings = []
    if not grounding.grounded:
        findings.append("ungrounded claim in artifact")
    if not access.passes:
        findings.append("plain-language/accessibility issue")
    if not pii_ok:
        findings.append("PII present in artifact")
    if state.get("needs_identity") and not state.get("identity_verified"):
        findings.append("personal data requested without verified identity")
    return {"grounding_report": grounding.to_audit_dict(),
            "accessibility_report": {"passes": access.passes, "issues": access.issues},
            "pii_ok": pii_ok, "quality_findings": findings, "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    if state.get("needs_identity") and not state.get("identity_verified"):
        return "human_review_gate"
    if state.get("quality_findings") and state.get("revision_count", 0) < 1:
        return "produce"
    return "human_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("needs_identity") and not state.get("identity_verified"):
        action = RecommendedAction.ESCALATE
    elif state.get("intent") in ("escalate",):
        action = RecommendedAction.ESCALATE
    else:
        action = RecommendedAction[WRITE_ACTION] if WRITE_ACTION in RecommendedAction.__members__ \
            else RecommendedAction.ESCALATE
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "human_review_gate",
            "completed_steps": state.get("completed_steps", []) + ["human_review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out = {"current_step": "finalize",
           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if str(action) == f"RecommendedAction.{WRITE_ACTION}" and approval:
        res = gw.call(claims, WRITE_TOOL, dict(WRITE_ARGS), approval=approval)
        out["write_result"] = res.result if res and res.allowed else None
        out["case_status"] = DONE_STATUS if (res and res.allowed) else "BLOCKED"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "PENDING_REVIEW"
    else:
        out["case_status"] = "PENDING_OFFICIAL" if WITHHELD_TOOL else "ESCALATED"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "case_status": out["case_status"],
        "grounded": state.get("grounding_report", {}).get("grounded"),
        "withheld_action_never_called": True}]
    return out


def run_until_gate(initial: Dict[str, Any]) -> Dict[str, Any]:
    s = dict(initial)
    s.update(intake(s)); s.update(classify_intent(s)); s.update(check_identity(s))
    for _ in range(2):
        s.update(gather(s)); s.update(produce(s)); s.update(compliance_check(s))
        if routing_decision(s) == "human_review_gate":
            break
        s["revision_count"] = s.get("revision_count", 0) + 1
    s.update(set_recommended_action(s)); s["_paused_at_gate"] = True
    return s


def resume(state: Dict[str, Any], approval=None) -> Dict[str, Any]:
    s = dict(state); s["_paused_at_gate"] = False
    if approval is not None:
        s["human_approval"] = approval
    s.update(finalize(s)); return s
