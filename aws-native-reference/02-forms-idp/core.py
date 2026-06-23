"""AWS-native deterministic core for Forms & Intelligent Document Processing (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'extract': ['upload', 'document', 'attachment', 'scan', 'extract'], 'validate': ['validate', 'check completeness', 'complete', 'missing field', 'incomplete'], 'assemble': ['assemble', 'fill the form', 'complete the form', 'submit form', 'apply'], 'status': ['status', 'where is my form', 'my submission']}
INTENT_ACTIONS = {'extract': 'EXTRACT', 'validate': 'VALIDATE', 'assemble': 'ASSEMBLE', 'status': 'STATUS_LOOKUP'}
WRITE_ACTIONS = ['ASSEMBLE']
DEFAULT_INTENT = 'assemble'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
