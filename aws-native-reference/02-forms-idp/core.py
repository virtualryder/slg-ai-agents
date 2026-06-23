"""AWS-native deterministic core for Forms & Intelligent Document Processing (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'extract': ['upload', 'document', 'attachment', 'scan', 'extract'], 'validate': ['validate', 'check', 'complete', 'missing', 'review'], 'assemble': ['assemble', 'fill', 'complete the form', 'submit form', 'apply'], 'status': ['status', 'where is my form', 'my application']}
DEFAULT_INTENT = 'assemble'
WRITE_ACTION = 'ASSEMBLE'
WITHHELD = None


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
