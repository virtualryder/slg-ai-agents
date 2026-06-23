"""AWS-native deterministic core for Permitting & Licensing (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'requirements': ['what do i need', 'requirement', 'required', 'do i need a permit'], 'status': ['status', 'where is my permit', 'holding'], 'apply': ['apply', 'start a permit', 'submit application', 'new permit'], 'route': ['route', 'send for review', 'route to']}
INTENT_ACTIONS = {'requirements': 'EXPLAIN_REQUIREMENTS', 'status': 'STATUS_LOOKUP', 'apply': 'CREATE_APPLICATION', 'route': 'ROUTE_REVIEW'}
WRITE_ACTIONS = ['CREATE_APPLICATION', 'ROUTE_REVIEW']
DEFAULT_INTENT = 'requirements'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
