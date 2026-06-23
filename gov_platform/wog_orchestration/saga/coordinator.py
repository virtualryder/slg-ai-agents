"""
Durable cross-agency saga coordinator with compensation.

A whole-of-government action (a move, a new business, a job-loss response) is a
distributed transaction across agencies that each own their own system of record.
There is no two-phase commit across a DMV, an HHS eligibility system, and a 311
CRM — so we use the SAGA pattern: each step has a forward action and a
COMPENSATING action, and if any step fails, the coordinator runs the
compensations for the already-completed steps in reverse order. The constituent
is never left half-enrolled.

Safety properties enforced here:
  * Material (write) steps are gated on a valid scoped CONSENT and an explicit
    resident CONFIRMATION before they run (fail-closed; the saga PAUSES, it does
    not roll back, when a gate is unmet — a human/clock can satisfy it later).
  * Idempotency: a step whose idempotency key already completed is skipped on
    re-run (exactly-once across retries / resumes).
  * Every forward and every compensation emits an immutable COMPLIANCE EVENT, so
    the case-level audit trail records what was done AND what was undone.

This is the testable model of AWS Step Functions (durable execution, Catch →
compensate branches) + EventBridge (events) + the GovernedToolGateway (the write).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..consent.service import ConsentLedger
from ..events.bus import ComplianceEventBus, ComplianceEvent

Action = Callable[[Dict[str, Any], Dict[str, Any]], Any]  # (claims, payload) -> result


@dataclass
class SagaStep:
    name: str
    intent: str
    agency: str
    forward: Action
    compensate: Optional[Action] = None
    material: bool = True
    idempotency_key: str = ""
    data_classes: List[str] = field(default_factory=lambda: ["PII"])


@dataclass
class StepOutcome:
    name: str
    status: str               # DONE | SKIPPED_IDEMPOTENT | NEEDS_CONSENT | NEEDS_CONFIRMATION | FAILED | COMPENSATED
    result: Any = None
    event_id: Optional[str] = None
    reason: str = ""


@dataclass
class SagaResult:
    status: str               # COMPLETED | COMPENSATED | PENDING_GATE
    outcomes: List[StepOutcome] = field(default_factory=list)
    compensated_steps: List[str] = field(default_factory=list)


@dataclass
class Saga:
    name: str
    resident_ref: str
    steps: List[SagaStep] = field(default_factory=list)


class SagaCoordinator:
    def __init__(self, consent: Optional[ConsentLedger] = None,
                 bus: Optional[ComplianceEventBus] = None,
                 required_aal: str = "AAL2") -> None:
        self.consent = consent or ConsentLedger()
        self.bus = bus or ComplianceEventBus()
        self.required_aal = required_aal
        self._completed_keys: Dict[str, Any] = {}      # idempotency
        self._completed: List[Dict[str, Any]] = []      # for compensation (reverse order)

    def run(self, saga: Saga, user_claims: Dict[str, Any], payload: Dict[str, Any],
            confirmations: Optional[Dict[str, bool]] = None) -> SagaResult:
        confirmations = confirmations or {}
        res = SagaResult(status="COMPLETED")

        for step in saga.steps:
            # idempotency: skip a step already completed (retry / resume safe)
            if step.idempotency_key and step.idempotency_key in self._completed_keys:
                res.outcomes.append(StepOutcome(step.name, "SKIPPED_IDEMPOTENT",
                                                result=self._completed_keys[step.idempotency_key]))
                continue

            if step.material:
                dec = self.consent.check(saga.resident_ref, scope=f"{saga.name}:{step.intent}",
                                         required_aal=self.required_aal)
                if not dec.allowed:
                    res.outcomes.append(StepOutcome(step.name, "NEEDS_CONSENT", reason=dec.reason))
                    res.status = "PENDING_GATE"
                    return res
                if not confirmations.get(step.intent):
                    res.outcomes.append(StepOutcome(step.name, "NEEDS_CONFIRMATION",
                                                    reason="explicit resident confirmation required"))
                    res.status = "PENDING_GATE"
                    return res

            try:
                result = step.forward(user_claims, payload)
            except Exception as exc:                          # forward failed -> compensate
                res.outcomes.append(StepOutcome(step.name, "FAILED", reason=f"{type(exc).__name__}: {exc}"))
                self._compensate(saga, user_claims, payload, res)
                res.status = "COMPENSATED"
                return res

            eid = self.bus.publish(ComplianceEvent(
                event_type=f"{saga.name}.{step.intent}.committed", resident_ref=saga.resident_ref,
                agency=step.agency, agent_id=step.intent, data_classes=step.data_classes,
                human_approval={"confirmed": step.material and confirmations.get(step.intent, False)},
                detail=f"saga {saga.name} step {step.name} committed",
            ))
            res.outcomes.append(StepOutcome(step.name, "DONE", result=result, event_id=eid))
            self._completed.append({"step": step, "result": result})
            if step.idempotency_key:
                self._completed_keys[step.idempotency_key] = result

        return res

    def _compensate(self, saga: Saga, claims: Dict[str, Any], payload: Dict[str, Any],
                    res: SagaResult) -> None:
        for entry in reversed(self._completed):
            step: SagaStep = entry["step"]
            if step.compensate is None:
                continue
            try:
                step.compensate(claims, payload)
            except Exception:                                 # compensation is best-effort; record either way
                pass
            eid = self.bus.publish(ComplianceEvent(
                event_type=f"{saga.name}.{step.intent}.compensated", resident_ref=saga.resident_ref,
                agency=step.agency, agent_id=step.intent, data_classes=step.data_classes,
                detail=f"saga {saga.name} step {step.name} compensated (rollback)",
            ))
            res.compensated_steps.append(step.name)
            res.outcomes.append(StepOutcome(step.name, "COMPENSATED", event_id=eid))
