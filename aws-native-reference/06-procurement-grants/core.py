"""AWS-native deterministic core for Procurement, Contracting & Grants (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'find': ['find a contract', 'vehicle', 'cooperative', 'funding', 'grant opportunity'], 'draft_rfp': ['draft', 'rfp', 'solicitation', 'write the scope', 'requirements doc'], 'compare': ['compare', 'evaluate', 'score', 'bids', 'proposals'], 'status': ['status', 'where is the solicitation', 'deadline']}
INTENT_ACTIONS = {'find': 'FIND_VEHICLES', 'draft_rfp': 'DRAFT_RFP', 'compare': 'COMPARE_BIDS', 'status': 'STATUS_LOOKUP'}
WRITE_ACTIONS = ['DRAFT_RFP']
DEFAULT_INTENT = 'draft_rfp'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
