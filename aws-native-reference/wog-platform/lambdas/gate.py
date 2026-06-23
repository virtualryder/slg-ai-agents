"""Gate Lambda — consent + explicit-confirmation gate for a material step.
In production this is a Step Functions waitForTaskToken state: the execution
pauses until a reviewer/resident satisfies it. Here it evaluates the consent
ledger + the confirmation flag passed in the execution input."""
from __future__ import annotations
from typing import Any, Dict
import _shared


def handler(event: Dict[str, Any], _ctx=None) -> Dict[str, Any]:
    import _shared as _s
    if _s.GOVGW is None:
        _s.bootstrap()
    spec = event["spec"]; ev = event["event"]; res_ref = event["resident_ref"]
    if not spec.get("material", True):
        return {**event, "proceed": True}
    dec = _shared.CONSENT.check(res_ref, scope=f"{ev}:{spec['intent']}", required_aal="AAL2")
    if not dec.allowed:
        return {**event, "proceed": False, "reason": f"NEEDS_CONSENT: {dec.reason}"}
    if not event.get("confirmations", {}).get(spec["intent"]):
        return {**event, "proceed": False, "reason": "NEEDS_CONFIRMATION"}
    return {**event, "proceed": True}
