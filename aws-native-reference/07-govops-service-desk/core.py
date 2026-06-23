"""AWS-native deterministic core for GovOps IT Service Desk & Modernization (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'support': ['how do i', 'password', 'vpn', 'access', 'help with'], 'incident': ['incident', 'outage', 'is down', 'error', 'broken'], 'runbook': ['restart', 'remediate', 'run the runbook', 'fix the service'], 'status': ['status', 'my ticket', 'ticket number']}
INTENT_ACTIONS = {'support': 'ANSWER', 'incident': 'CREATE_TICKET', 'runbook': 'RUN_RUNBOOK', 'status': 'STATUS_LOOKUP'}
WRITE_ACTIONS = ['CREATE_TICKET', 'RUN_RUNBOOK']
DEFAULT_INTENT = 'support'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
