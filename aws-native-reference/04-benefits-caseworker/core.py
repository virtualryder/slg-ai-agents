"""AWS-native deterministic core for Benefits / HHS Caseworker Assist (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'prescreen': ['qualify', 'eligible', 'prescreen', 'what benefits'], 'status': ['status', 'my case', 'my application'], 'apply': ['apply', 'application', 'renew', 'renewal'], 'notice': ['notice', 'letter', 'request for information', 'rfi']}
DEFAULT_INTENT = 'prescreen'
WRITE_ACTION = 'CREATE_APPLICATION'
WITHHELD = 'eligibility.adjudicate'


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
