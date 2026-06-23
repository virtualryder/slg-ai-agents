# agent/nodes.py
# ============================================================
# Node logic for the Resident Services & 311 workflow.
#
# Each node is a pure function (state -> partial state update). The logic runs in
# EXTRACT_MODE=demo with no LLM call (deterministic keyword routing + templated,
# grounded answers from retrieved sources), and uses the LLM factory + gateway
# tools in live mode. Keeping nodes langgraph-free makes them unit-testable
# without the framework; graph.py wires them into a StateGraph with a
# framework-enforced HITL interrupt.
# ============================================================
from __future__ import annotations

import os
from typing import Any, Dict

from governance.accessibility.wcag import check_html, check_plain_language
from governance.grounding import verify_grounding
from slg_agent_platform.pii import mask

from tools import gateway_tools as gw
from agent.state import RecommendedAction

# Intents that require an authenticated, consented resident before any disclosure.
_PERSONAL_INTENTS = {"status_lookup"}
_INTENT_KEYWORDS = {
    "status_lookup": ["status", "my application", "my case", "my request", "where is"],
    "appointment": ["appointment", "schedule", "book", "visit", "counter"],
    "service_request": ["pothole", "report", "broken", "missed", "graffiti", "streetlight"],
    "escalate": ["lawsuit", "discrimination", "emergency", "urgent complaint"],
}


def _demo() -> bool:
    return os.getenv("EXTRACT_MODE", "demo").strip().lower() == "demo"


def intake(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "current_step": "intake",
        "completed_steps": state.get("completed_steps", []) + ["intake"],
        "channel": state.get("channel", "WEB"),
        "locale": state.get("locale", "en-US"),
        "revision_count": state.get("revision_count", 0),
        "case_status": "INTAKE",
    }


def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    text = (state.get("raw_request") or "").lower()
    intent = "policy_question"
    for cand, kws in _INTENT_KEYWORDS.items():
        if any(k in text for k in kws):
            intent = cand
            break
    needs_identity = intent in _PERSONAL_INTENTS
    return {"intent": intent, "needs_identity": needs_identity,
            "current_step": "classify_intent",
            "completed_steps": state.get("completed_steps", []) + ["classify_intent"]}


def retrieve_knowledge(state: Dict[str, Any]) -> Dict[str, Any]:
    claims = state.get("acting_user_claims", {})
    sources = gw.search_policy(claims, state.get("raw_request", ""))
    return {"retrieved_sources": sources, "current_step": "retrieve_knowledge",
            "completed_steps": state.get("completed_steps", []) + ["retrieve_knowledge"]}


def check_identity(state: Dict[str, Any]) -> Dict[str, Any]:
    if not state.get("needs_identity"):
        return {"identity_verified": True, "current_step": "check_identity",
                "completed_steps": state.get("completed_steps", []) + ["check_identity"]}
    claims = state.get("acting_user_claims", {})
    assertion = state.get("identity_assertion", "")
    res = gw.verify_resident(claims, assertion) if assertion else {"verified": False}
    return {"identity_verified": bool(res.get("verified")),
            "resident_ref": res.get("resident_id"),
            "current_step": "check_identity",
            "completed_steps": state.get("completed_steps", []) + ["check_identity"]}


def draft_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    sources = state.get("retrieved_sources", [])
    if _demo() or not sources:
        if sources:
            top = sources[0]
            answer = top.get("snippet", "")
            citations = [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources]
            drafted_by = "demo-stub"
        else:
            answer = "I could not find an authoritative source. Routing you to a city representative."
            citations = []
            drafted_by = "demo-stub"
    else:  # pragma: no cover - live LLM path
        from slg_agent_platform.llm_factory import get_llm
        from agent.prompts import ANSWER_PROMPT
        llm = get_llm("narrative")
        ctx = "\n".join(f"- {s.get('title')}: {s.get('snippet')} ({s.get('url')})" for s in sources)
        msg = llm.invoke(f"{ANSWER_PROMPT}\n\nSOURCES:\n{ctx}\n\nQUESTION: {state.get('raw_request')}")
        answer = getattr(msg, "content", str(msg))
        citations = [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources]
        drafted_by = "bedrock"
    return {"draft_answer": answer, "citations": citations, "answer_drafted_by": drafted_by,
            "current_step": "draft_answer",
            "completed_steps": state.get("completed_steps", []) + ["draft_answer"]}


def compliance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    answer = state.get("draft_answer", "")
    grounding = verify_grounding(answer, {"sources": state.get("retrieved_sources", [])})
    access = check_plain_language(answer)
    pii_ok = mask(answer) == answer  # answer should carry no raw identifiers
    findings = []
    if not grounding.grounded:
        findings.append("ungrounded claims present")
    if not access.passes:
        findings.append("accessibility/plain-language issue")
    if not pii_ok:
        findings.append("PII detected in public answer")
    # personal disclosure without verified identity is a hard fail
    if state.get("needs_identity") and not state.get("identity_verified"):
        findings.append("personal data requested without verified identity")
    return {"grounding_report": grounding.to_audit_dict(),
            "accessibility_report": {"passes": access.passes, "issues": access.issues},
            "pii_ok": pii_ok, "quality_findings": findings,
            "current_step": "compliance_check",
            "completed_steps": state.get("completed_steps", []) + ["compliance_check"]}


def routing_decision(state: Dict[str, Any]) -> str:
    """Conditional edge target: revise (bounded), or proceed to the human gate."""
    findings = state.get("quality_findings", [])
    if state.get("needs_identity") and not state.get("identity_verified"):
        return "human_review_gate"  # surfaced to staff with VERIFY_IDENTITY action
    if findings and state.get("revision_count", 0) < 1:
        return "draft_answer"
    return "human_review_gate"


def set_recommended_action(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("needs_identity") and not state.get("identity_verified"):
        action = RecommendedAction.VERIFY_IDENTITY
    elif state.get("intent") == "service_request":
        action = RecommendedAction.CREATE_REQUEST
    elif state.get("intent") == "appointment":
        action = RecommendedAction.BOOK_APPOINTMENT
    elif state.get("intent") == "escalate":
        action = RecommendedAction.ESCALATE
    else:
        action = RecommendedAction.ANSWER
    bump = 1 if "draft_answer" in state.get("completed_steps", []) else 0
    return {"recommended_action": action,
            "revision_count": state.get("revision_count", 0) + (1 if state.get("quality_findings") else 0),
            "current_step": "human_review_gate",
            "completed_steps": state.get("completed_steps", []) + ["human_review_gate"]}


def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
    action = state.get("recommended_action")
    approval = state.get("human_approval")  # supplied by reviewer on resume
    claims = state.get("acting_user_claims", {})
    out: Dict[str, Any] = {"current_step": "finalize",
                           "completed_steps": state.get("completed_steps", []) + ["finalize"]}
    if action == RecommendedAction.CREATE_REQUEST and approval:
        res = gw.create_service_request(claims, {"type": state.get("intent", "General")}, approval=approval)
        out["service_request_id"] = getattr(res, "result", {}).get("request_id") if res.allowed else None
        out["case_status"] = "REQUEST_CREATED"
    elif action == RecommendedAction.BOOK_APPOINTMENT and approval:
        res = gw.book_appointment(claims, {"service": "counter", "slot": state.get("slot", "")}, approval=approval)
        out["appointment_id"] = getattr(res, "result", {}).get("appointment_id") if res.allowed else None
        out["case_status"] = "REQUEST_CREATED"
    elif action == RecommendedAction.ESCALATE:
        out["case_status"] = "ESCALATED"
    elif action == RecommendedAction.VERIFY_IDENTITY:
        out["case_status"] = "PENDING_REVIEW"
    else:
        out["case_status"] = "ANSWERED"
    out["audit_trail"] = state.get("audit_trail", []) + [{
        "action": str(action), "case_status": out["case_status"],
        "drafted_by": state.get("answer_drafted_by"),
        "grounded": state.get("grounding_report", {}).get("grounded"),
    }]
    return out
