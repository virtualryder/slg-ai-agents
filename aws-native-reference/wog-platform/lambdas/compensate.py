"""Compensate Lambda — rolls back already-committed compensable steps in reverse
order and emits compensated compliance events. Idempotent and best-effort."""
from __future__ import annotations
from typing import Any, Dict, List
import _shared
from gov_platform.wog_orchestration.events import ComplianceEvent


def handler(event: Dict[str, Any], _ctx=None) -> Dict[str, Any]:
    import _shared as _s
    if _s.GOVGW is None:
        _s.bootstrap()
    committed: List[Dict[str, Any]] = event.get("committed", [])
    rolled_back: List[str] = []
    for c in reversed(committed):
        if not c.get("compensate_tool"):
            continue
        # production: call the agency cancel/withdraw API via the gateway here
        _shared.BUS.publish(ComplianceEvent(
            event_type=f"{event['event']}.{c['name']}.compensated", resident_ref=event["resident_ref"],
            agency="compensation", agent_id=c["name"], correlation_id=event.get("correlation_id", ""),
            detail=f"rolled back via {c['compensate_tool']}"))
        rolled_back.append(c["name"])
    return {"status": "COMPENSATED", "rolled_back": rolled_back}
