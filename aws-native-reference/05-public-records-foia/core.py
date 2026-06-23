"""AWS-native deterministic core for Public Records / FOIA & Redaction (Strands + Step Functions)."""
from __future__ import annotations

INTENT_KEYWORDS = {'search': ['find', 'search', 'records about', 'responsive'], 'classify': ['classify', 'responsive', 'duplicate'], 'redact': ['redact', 'exemption', 'protect'], 'package': ['package', 'produce', 'assemble', 'release package'], 'status': ['status', 'my request', 'clock', 'deadline']}
DEFAULT_INTENT = 'search'
WRITE_ACTION = 'ASSEMBLE_PACKAGE'
WITHHELD = 'records.release'


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
