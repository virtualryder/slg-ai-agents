"""
Grounding verification — claim traceability for resident- and official-facing text.

A constituent-facing answer, a drafted deficiency notice, an RFP section, or an
incident summary must contain ONLY claims traceable to the state that produced it.
An LLM hallucination in a public answer (a wrong fee, a fabricated deadline, an
invented department) is a public-trust and potentially legal defect.
verify_grounding flags any number or capitalized multi-word entity in the text
that is not traceable to the input state, so a human reviewer (and CI) can catch
fabricated amounts, dates, or agency names before anything reaches a resident.

This is a deterministic control (no LLM, no API key) so it runs in CI and is
includable in an accreditation/ATO evidence package.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

# Public-sector entities that are always acceptable without appearing in state.
_ENTITY_ALLOWLIST = {
    "United States", "Department of Justice", "Internal Revenue Service",
    "Social Security Administration", "Public Works", "Department of Motor Vehicles",
    "Building Department", "Planning Department", "Fire Marshal", "City Council",
    "County Clerk", "Freedom of Information", "Public Records", "Open Records",
    "Americans with Disabilities Act", "Real ID", "Federal Emergency Management Agency",
    "Supplemental Nutrition Assistance Program", "Temporary Assistance",
    "Resident Services", "Records Officer", "Procurement Officer", "Permit Official",
    "Eligibility Caseworker", "Eligibility Supervisor",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "The", "This", "These", "Per", "Resident", "Applicant", "Department", "Agency",
}

# Small structural numbers commonly used in SLG processes (business days, etc.).
_NUMBER_ALLOWLIST = {"3", "5", "7", "10", "14", "15", "21", "30", "45", "60", "90"}

_NUMBER_RE = re.compile(r"\$?\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\$?\b\d+(?:\.\d+)?%?\b")
_ENTITY_RE = re.compile(r"\b(?:[A-Z][a-zA-Z&'-]+(?:\s+[A-Z][a-zA-Z&'-]+)+)\b")


@dataclass
class GroundingReport:
    ungrounded_numbers: List[str] = field(default_factory=list)
    ungrounded_entities: List[str] = field(default_factory=list)
    checked_numbers: int = 0
    checked_entities: int = 0

    @property
    def grounded(self) -> bool:
        return not self.ungrounded_numbers and not self.ungrounded_entities

    def to_audit_dict(self) -> Dict[str, Any]:
        return {
            "grounded": self.grounded,
            "ungrounded_numbers": self.ungrounded_numbers,
            "ungrounded_entities": self.ungrounded_entities,
            "checked_numbers": self.checked_numbers,
            "checked_entities": self.checked_entities,
        }


def _normalize_number(tok: str) -> str:
    return tok.replace("$", "").replace(",", "").replace("%", "").rstrip(".")


def _state_number_corpus(state: Dict[str, Any]) -> Set[str]:
    blob = json.dumps(state, default=str)
    nums: Set[str] = set()
    for tok in _NUMBER_RE.findall(blob):
        n = _normalize_number(tok)
        nums.add(n)
        try:
            f = float(n)
            nums.add(f"{f:g}")
            if f == int(f):
                nums.add(str(int(f)))
        except ValueError:
            pass
    return nums


def verify_grounding(text: str, state: Dict[str, Any]) -> GroundingReport:
    report = GroundingReport()
    if not text:
        return report

    state_numbers = _state_number_corpus(state)
    state_text = json.dumps(state, default=str).lower()

    for tok in _NUMBER_RE.findall(text):
        n = _normalize_number(tok)
        try:
            value = float(n)
        except ValueError:
            continue
        if value <= 2:
            continue
        if n in _NUMBER_ALLOWLIST or f"{value:g}" in _NUMBER_ALLOWLIST:
            continue
        report.checked_numbers += 1
        aliases = {n, f"{value:g}"}
        if value == int(value):
            aliases.add(str(int(value)))
        if not aliases & state_numbers:
            report.ungrounded_numbers.append(tok)

    leading_stop = {"Between", "On", "In", "At", "During", "After", "Before",
                    "Within", "The", "This", "These", "Per", "From", "By", "Under", "Each", "Your"}
    for ent in set(_ENTITY_RE.findall(text)):
        words = ent.split()
        while words and words[0] in leading_stop:
            words = words[1:]
        if len(words) < 2:
            continue
        ent = " ".join(words)
        if ent in _ENTITY_ALLOWLIST or any(ent.startswith(a + " ") for a in _ENTITY_ALLOWLIST):
            continue
        report.checked_entities += 1
        if ent.lower() not in state_text:
            report.ungrounded_entities.append(ent)

    report.ungrounded_numbers.sort()
    report.ungrounded_entities.sort()
    return report
