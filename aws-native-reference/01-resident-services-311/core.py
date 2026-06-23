"""
AWS-native deterministic core for Agent 01 (Strands + Step Functions).

The Step Functions state machine IS the agent: each Lambda calls one of these
pure functions, and the human gate is a waitForTaskToken pause. The same
governance controls (grounding, accessibility) and the same deny-by-default
gateway semantics apply; this module keeps the non-LLM logic deterministic and
unit-testable for inclusion in an ATO evidence package.
"""
from __future__ import annotations
from typing import Any, Dict

INTENT_KEYWORDS = {
    "status_lookup": ["status", "my application", "my case", "my request"],
    "appointment": ["appointment", "schedule", "book"],
    "service_request": ["pothole", "report", "broken", "missed", "graffiti"],
    "escalate": ["lawsuit", "discrimination", "emergency"],
}
PERSONAL_INTENTS = {"status_lookup"}


def classify(text: str) -> str:
    t = (text or "").lower()
    for intent, kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws):
            return intent
    return "policy_question"


def needs_identity(intent: str) -> bool:
    return intent in PERSONAL_INTENTS


def recommended_action(intent: str, identity_verified: bool) -> str:
    if needs_identity(intent) and not identity_verified:
        return "VERIFY_IDENTITY"
    return {"service_request": "CREATE_REQUEST", "appointment": "BOOK_APPOINTMENT",
            "escalate": "ESCALATE"}.get(intent, "ANSWER")


def is_write_action(action: str) -> bool:
    return action in {"CREATE_REQUEST", "BOOK_APPOINTMENT"}
