"""AWS-native deterministic core for Procurement, Contracting & Grants (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'find': ['find a contract', 'vehicle', 'cooperative', 'funding', 'grant opportunity'], 'draft_rfp': ['draft', 'rfp', 'solicitation', 'requirements', 'scope'], 'compare': ['compare', 'evaluate', 'score', 'bids', 'proposals'], 'status': ['status', 'where is', 'deadline']}
DEFAULT_INTENT = 'draft_rfp'
WRITE_ACTION = 'DRAFT_RFP'
WITHHELD = 'procurement.award'


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
