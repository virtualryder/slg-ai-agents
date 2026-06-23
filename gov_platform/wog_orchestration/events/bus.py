"""
Compliance event bus — the unified, immutable case-level audit spine.

Every material step across every agency emits a ComplianceEvent carrying who,
what, which agency/agent, the data classes touched, and the human-approval
linkage. In production this is Amazon EventBridge (routing) + an append-only
sink (DynamoDB deny Update/Delete, with WORM snapshots in S3 Object Lock). Here
it is an in-memory append-only log so the model is testable. Events are PII-masked
on write via the platform masker.
"""
from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from slg_agent_platform.pii import mask


@dataclass
class ComplianceEvent:
    event_type: str
    resident_ref: str
    agency: str
    agent_id: str
    data_classes: List[str] = field(default_factory=list)   # e.g. ["PII","FTI"]
    human_approval: Dict[str, Any] = field(default_factory=dict)
    detail: str = ""
    correlation_id: str = ""   # case-level correlation (one life-event / one case)


class ComplianceEventBus:
    def __init__(self) -> None:
        self._log: List[Dict[str, Any]] = []
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.append(fn)

    def publish(self, ev: ComplianceEvent) -> str:
        eid = f"EVT-{uuid.uuid4().hex[:10]}"
        rec = {
            "event_id": eid,
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "event_type": ev.event_type, "resident_ref": ev.resident_ref,
            "agency": ev.agency, "agent_id": ev.agent_id,
            "data_classes": ev.data_classes, "human_approval": ev.human_approval,
            "correlation_id": ev.correlation_id,
            "detail": mask(ev.detail),
        }
        self._log.append(rec)
        for fn in self._subscribers:
            fn(rec)
        return eid

    @property
    def log(self) -> List[Dict[str, Any]]:
        return list(self._log)
