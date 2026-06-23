"""AWS-native deterministic core for GovOps IT Service Desk & Modernization (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'support': ['how do i', 'password', 'vpn', 'access', 'help'], 'incident': ['incident', 'outage', 'down', 'error', 'broken'], 'runbook': ['restart', 'remediate', 'run the runbook', 'fix the service'], 'status': ['status', 'my ticket', 'where is']}
DEFAULT_INTENT = 'support'
WRITE_ACTION = 'CREATE_TICKET'
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
