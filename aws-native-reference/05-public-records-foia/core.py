"""AWS-native deterministic core for Public Records / FOIA & Redaction (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'search': ['find', 'search', 'records about', 'responsive'], 'classify': ['classify', 'responsive', 'duplicate'], 'redact': ['redact', 'exemption', 'protect', 'redaction'], 'package': ['package', 'produce', 'assemble the package', 'production'], 'status': ['status', 'my request', 'clock', 'deadline']}
INTENT_ACTIONS = {'search': 'SEARCH', 'classify': 'CLASSIFY', 'redact': 'PROPOSE_REDACTION', 'package': 'ASSEMBLE_PACKAGE', 'status': 'STATUS_LOOKUP'}
WRITE_ACTIONS = ['ASSEMBLE_PACKAGE']
DEFAULT_INTENT = 'search'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
