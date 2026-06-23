"""
Life-event orchestrator — durable, multi-agency workflows with explicit consent
and explicit resident confirmation before each MATERIAL action.

Organizes services around a life event (moving, new child, start a business, lose
a job, disaster, bereavement) instead of agency structure. It composes the
platform: the A2A Supervisor (routing, no tool grants) + the ConsentLedger +
the ComplianceEventBus. The critical safety property: a material step (one that
writes to a system of record) is NEVER executed without (a) a valid scoped consent
and (b) an explicit resident confirmation. Read/informational steps flow freely.

In production this maps to AWS Step Functions (durable execution) + EventBridge
(events) + AgentCore A2A (specialist invocation), with the same gates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from slg_agent_platform.a2a import Supervisor, LIFE_EVENTS, INTENT_ROUTES
from ..consent.service import ConsentLedger
from ..events.bus import ComplianceEventBus, ComplianceEvent

# Which intents in a life-event are MATERIAL (write) vs informational (read).
MATERIAL_INTENTS = {"service_request", "form", "application", "permit", "benefits",
                    "appointment", "incident_report"}


@dataclass
class StepResult:
    intent: str
    agent_id: Optional[str]
    status: str           # DONE | NEEDS_CONFIRMATION | NEEDS_CONSENT | SKIPPED | UNROUTED
    output: Any = None
    event_id: Optional[str] = None
    reason: str = ""


@dataclass
class LifeEventOrchestrator:
    supervisor: Supervisor
    consent: ConsentLedger = field(default_factory=ConsentLedger)
    bus: ComplianceEventBus = field(default_factory=ComplianceEventBus)

    def run(self, event: str, user_claims: Dict[str, Any], payload: Dict[str, Any],
            confirmations: Optional[Dict[str, bool]] = None,
            required_aal: str = "AAL2") -> List[StepResult]:
        confirmations = confirmations or {}
        resident_ref = payload.get("resident_ref", "RES-unknown")
        results: List[StepResult] = []

        for intent in LIFE_EVENTS.get(event, []):
            agent_id = INTENT_ROUTES.get(intent)
            material = intent in MATERIAL_INTENTS

            if material:
                # 1. consent gate
                dec = self.consent.check(resident_ref, scope=f"{event}:{intent}",
                                         required_aal=required_aal)
                if not dec.allowed:
                    results.append(StepResult(intent, agent_id, "NEEDS_CONSENT", reason=dec.reason))
                    continue
                # 2. explicit resident confirmation gate
                if not confirmations.get(intent):
                    results.append(StepResult(intent, agent_id, "NEEDS_CONFIRMATION",
                                              reason="explicit resident confirmation required"))
                    continue

            routed = self.supervisor.route_intent(intent, user_claims, payload)
            if not routed.handled:
                results.append(StepResult(intent, agent_id, "UNROUTED", reason=routed.reason))
                continue

            eid = self.bus.publish(ComplianceEvent(
                event_type=f"{event}.{intent}", resident_ref=resident_ref,
                agency=agent_id or "wog", agent_id=agent_id or "wog",
                data_classes=payload.get("data_classes", ["PII"]),
                human_approval={"confirmed": material and confirmations.get(intent, False)},
                detail=f"life-event {event} step {intent}",
            ))
            results.append(StepResult(intent, agent_id, "DONE", output=routed.output, event_id=eid))
        return results


    def run_saga(self, saga, user_claims, payload, confirmations=None):
        """
        Run a cross-agency Saga through the durable coordinator, sharing this
        orchestrator's consent ledger and compliance event bus so the evidence
        trail is unified. Use this for life-events that need compensation/rollback
        across agencies (vs. run(), which is the simple sequential path).
        """
        from ..saga.coordinator import SagaCoordinator
        co = SagaCoordinator(consent=self.consent, bus=self.bus, required_aal="AAL2")
        return co.run(saga, user_claims, payload, confirmations=confirmations)

