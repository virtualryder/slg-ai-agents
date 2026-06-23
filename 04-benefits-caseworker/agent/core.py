# agent/core.py — Benefits / HHS Caseworker Assist
# Framework-free workflow (runs in EXTRACT_MODE=demo with no LLM). Each intent maps
# to a distinct recommended action, system-of-record tool, and outcome status.
from __future__ import annotations
import os
from typing import Any, Dict

from governance.accessibility.wcag import check_plain_language
from governance.grounding import verify_grounding
from slg_agent_platform.pii import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction

INTENTS = {'prescreen': ['qualify', 'eligible', 'prescreen', 'what benefits', 'might i get'], 'status': ['status', 'my case', 'my application'], 'apply': ['apply', 'start an application', 'renew', 'renewal'], 'notice': ['notice', 'letter', 'request for information', 'rfi', 'send a notice']}
INTENT_ACTIONS = {'prescreen': {'action': 'PRESCREEN', 'tool': 'eligibility.screen', 'args': {}, 'write': False, 'done': 'PRESCREENED'}, 'status': {'action': 'STATUS_LOOKUP', 'tool': 'eligibility.get_case', 'args': {'case_id': 'APP-778120'}, 'write': False, 'done': 'STATUS_PROVIDED'}, 'apply': {'action': 'CREATE_APPLICATION', 'tool': 'eligibility.create_application', 'args': {'program': 'SNAP'}, 'write': True, 'done': 'APPLICATION_CREATED'}, 'notice': {'action': 'DRAFT_NOTICE', 'tool': 'eligibility.generate_notice', 'args': {'type': 'Request for Information'}, 'write': True, 'done': 'NOTICE_DRAFTED'}}
PERSONAL_INTENTS = set(['status'])
DEFAULT_INTENT = 'prescreen'
CONTEXT_READ_TOOL = 'eligibility.screen'
CONTEXT_READ_ARGS = {}
WITHHELD_TOOL = 'eligibility.adjudicate'   # legally consequential action the agent may NOT call


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def _spec(state: Dict[str, Any]) -> Dict[str, Any]:
    return INTENT_ACTIONS.get(state.get("intent"), INTENT_ACTIONS[DEFAULT_INTENT])


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
    spec = _spec(state)
    # read-action intents call their own tool; write intents read a safe context tool to ground the draft
    if spec.get("tool") and not spec["write"]:
        tool, args = spec["tool"], spec.get("args", {})
    else:
        tool, args = CONTEXT_READ_TOOL, CONTEXT_READ_ARGS
    res = gw.call(claims, tool, dict(args)) if tool else None
    return {"gathered": (res.result if res and res.allowed else None),
            "current_step": "gather",
            "completed_steps": state.get("completed_steps", []) + ["gather"]}


def produce(state: Dict[str, Any]) -> Dict[str, Any]:
    artifact = {"summary": "Artifact prepared from the approved source record.",
                "intent": state.get("intent"), "source": state.get("gathered"),
                "withheld_action": WITHHELD_TOOL}
    return {"artifact": artifact, "artifact_text": artifact["summary"], "produced_by": "demo-stub",
            "current_step": "produce",
            "completed_steps": state.get("completed_steps", []) + ["produce"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("artifact_text", "")
    grounding = verify_grounding(text, {"src": state.get("gathered")})
    access = check_plain_language(text)
    pii_ok = mask(text) == text
    findings = []
    if not grounding.grounded: findings.append("ungrounded claim in artifact")
    if not access.passes: findings.append("plain-language/accessibility issue")
    if not pii_ok: findings.append("PII present in artifact")
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
    spec = _spec(state)
    if state.get("needs_identity") and not state.get("identity_verified") \
            and "VERIFY_IDENTITY" in RecommendedAction.__members__:
        action = RecommendedAction.VERIFY_IDENTITY
    elif state.get("intent") == "escalate":
        action = RecommendedAction.ESCALATE
    else:
        action = RecommendedAction[spec["action"]]
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "human_review_gate",
            "completed_steps": state.get("completed_steps", []) + ["human_review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    spec = _spec(state)
    approval = state.get("human_approval")
    claims = state.get("acting_user_claims", {})
    out = {"current_step": "finalize",
           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if state.get("needs_identity") and not state.get("identity_verified"):
        out["case_status"] = "PENDING_REVIEW"
    elif spec["write"]:
        if approval:
            res = gw.call(claims, spec["tool"], dict(spec.get("args", {})), approval=approval)
            if res and res.allowed:
                out["write_result"] = res.result
                out["case_status"] = spec["done"]
            else:  # e.g. acting role not entitled to a high-risk tool (run_runbook needs SRE)
                out["case_status"] = "BLOCKED_NEEDS_APPROVER"
        else:
            out["case_status"] = "PENDING_APPROVAL"
    else:
        out["case_status"] = spec["done"]   # read-action intents complete without a write
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(state.get("recommended_action")), "case_status": out["case_status"],
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
    if approval is not None: s["human_approval"] = approval
    s.update(finalize(s)); return s
