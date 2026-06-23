"""AWS-native deterministic core for Public Safety / Public Health Case & Report (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'summarize': ['summarize', 'incident', 'narrative', 'body-cam'], 'report': ['report', 'write up', 'draft report', 'after-action'], 'surveillance': ['how many', 'cases', 'surveillance', 'query', 'outbreak', 'vaccination']}
DEFAULT_INTENT = 'summarize'
WRITE_ACTION = 'DRAFT_REPORT'
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
