"""AWS-native deterministic core for Permitting & Licensing (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'requirements': ['what do i need', 'requirement', 'required', 'do i need a permit'], 'status': ['status', 'where is my permit', 'holding'], 'apply': ['apply', 'application', 'submit', 'start a permit'], 'route': ['route', 'review', 'send to']}
DEFAULT_INTENT = 'requirements'
WRITE_ACTION = 'CREATE_APPLICATION'
WITHHELD = 'permitting.issue_permit'


def classify(text: str) -> str:
    t = (text or "").lower()
    for intent, kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws):
            return intent
    return DEFAULT_INTENT


def recommended_action(intent: str) -> str:
    return {"escalate": "ESCALATE"}.get(intent, WRITE_ACTION)


def is_write_action(action: str) -> bool:
    return action == WRITE_ACTION
