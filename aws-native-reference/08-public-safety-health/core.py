"""AWS-native deterministic core for Public Safety / Public Health Case & Report (Strands + Step Functions)."""
from __future__ import annotations
INTENT_KEYWORDS = {'summarize': ['summarize', 'incident narrative', 'body-cam', 'summarize the incident'], 'report': ['report', 'write up', 'draft the report', 'after-action'], 'surveillance': ['how many', 'cases', 'surveillance', 'query', 'outbreak', 'vaccination rate']}
INTENT_ACTIONS = {'summarize': 'SUMMARIZE', 'report': 'DRAFT_REPORT', 'surveillance': 'RUN_QUERY'}
WRITE_ACTIONS = ['DRAFT_REPORT']
DEFAULT_INTENT = 'summarize'
def classify(text: str) -> str:
    t=(text or "").lower()
    for intent,kws in INTENT_KEYWORDS.items():
        if any(k in t for k in kws): return intent
    return DEFAULT_INTENT
def recommended_action(intent: str) -> str:
    return INTENT_ACTIONS.get(intent, INTENT_ACTIONS[DEFAULT_INTENT])
def is_write_action(action: str) -> bool:
    return action in WRITE_ACTIONS
