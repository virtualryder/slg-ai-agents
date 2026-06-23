"""AWS-native deterministic core for Benefits / HHS Caseworker Assist (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'prescreen': ['qualify', 'eligible', 'prescreen', 'what benefits', 'might i get'], 'status': ['status', 'my case', 'my application'], 'apply': ['apply', 'start an application', 'renew', 'renewal'], 'notice': ['notice', 'letter', 'request for information', 'rfi', 'send a notice']}
INTENT_ACTIONS = {'prescreen': 'PRESCREEN', 'status': 'STATUS_LOOKUP', 'apply': 'CREATE_APPLICATION', 'notice': 'DRAFT_NOTICE'}
WRITE_ACTIONS = ['CREATE_APPLICATION', 'DRAFT_NOTICE']
DEFAULT_INTENT = 'prescreen'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
