"""
Compliance evidence — the case-level audit trail, assembled from events.

The compliance event bus captures every material step (and every rollback). For
an audit, a public-records request, or an appeal, an agency needs the events for
ONE case (one life-event, one application) assembled in order, with each event
annotated by its data classes and the resulting RETENTION obligation. This module
turns the raw event stream into that evidence package.

Retention is data-class driven (illustrative defaults; the agency's records
officer sets the real schedule):
  CJI  -> per CJIS / state criminal-justice retention
  FTI  -> IRS Pub 1075 (min 6 years typical for FTI-derived records)
  PHI  -> HIPAA (6 years from creation / last effective date)
  EDU  -> FERPA / state education retention
  PII  -> state public-records schedule
  PUBLIC -> public-records schedule
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# Event-type taxonomy (suffixes); full type is "<lifeevent>.<intent>.<suffix>".
COMMITTED = "committed"
COMPENSATED = "compensated"
DENIED = "denied"
CONSENT_RECORDED = "consent_recorded"

# Illustrative retention floors in days (records officer overrides per schedule).
DATA_CLASS_RETENTION_DAYS: Dict[str, int] = {
    "CJI": 365 * 7,
    "FTI": 365 * 6,
    "PHI": 365 * 6,
    "EDU": 365 * 5,
    "PII": 365 * 3,
    "PUBLIC": 365 * 3,
}


def retention_days(data_classes: List[str]) -> int:
    """The binding retention is the MAX across all data classes touched."""
    return max((DATA_CLASS_RETENTION_DAYS.get(dc, 365 * 3) for dc in (data_classes or ["PII"])), default=365 * 3)


@dataclass
class EvidencePackage:
    resident_ref: str
    correlation_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    binding_retention_days: int = 0
    data_classes: List[str] = field(default_factory=list)

    @property
    def was_compensated(self) -> bool:
        return any(e["event_type"].endswith(f".{COMPENSATED}") for e in self.events)

    def to_audit_dict(self) -> Dict[str, Any]:
        return {
            "resident_ref": self.resident_ref,
            "correlation_id": self.correlation_id,
            "event_count": len(self.events),
            "data_classes": sorted(set(self.data_classes)),
            "binding_retention_days": self.binding_retention_days,
            "was_compensated": self.was_compensated,
            "events": self.events,
        }


def assemble_evidence(bus, resident_ref: str, correlation_id: str = "") -> EvidencePackage:
    """Build the ordered, retention-annotated case-level trail for one resident/case."""
    selected = [
        e for e in bus.log
        if e.get("resident_ref") == resident_ref
        and (not correlation_id or e.get("correlation_id") == correlation_id)
    ]
    selected.sort(key=lambda e: e.get("ts", ""))
    classes: List[str] = []
    for e in selected:
        classes.extend(e.get("data_classes", []))
    pkg = EvidencePackage(resident_ref=resident_ref, correlation_id=correlation_id,
                          events=selected, data_classes=classes)
    pkg.binding_retention_days = retention_days(classes)
    return pkg
