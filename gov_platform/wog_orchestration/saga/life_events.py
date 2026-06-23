"""
Declarative life-event templates — one definition, two runtimes.

A life event is a list of StepSpecs (pure data: which agency, which governed
tool, purpose, args, idempotency, compensation tool). The SAME spec list drives:
  * the in-process SagaCoordinator (build_saga -> SagaSteps with forward/compensate
    bound to a GovernedToolGateway), and
  * the AWS-native path (each spec is shipped to a `step` Lambda as JSON, and the
    Step Functions saga loops over the list with a Catch -> compensate branch).

Keeping steps declarative is what lets the local demo, the unit tests, and the
deployed state machine all execute the identical workflow. Adding a life event is
a data change here; adding an agency is a new catalog entry + adapter.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .coordinator import Saga, SagaStep


@dataclass(frozen=True)
class StepSpec:
    name: str
    intent: str
    agency: str
    agent_id: str
    tool: str
    purpose: str
    args: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: str = ""
    data_classes: tuple = ("PII",)
    material: bool = True
    compensate_tool: Optional[str] = None     # the real cancel/withdraw endpoint

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self); d["data_classes"] = list(self.data_classes); return d


def spec_from_dict(d: Dict[str, Any]) -> StepSpec:
    d = dict(d); d["data_classes"] = tuple(d.get("data_classes", ("PII",)))
    return StepSpec(**d)


# ── The templates ─────────────────────────────────────────────────────────────
LIFE_EVENT_TEMPLATES: Dict[str, List[StepSpec]] = {
    "moving": [
        StepSpec("assemble_coa", "form", "Shared Services", "02-forms-idp",
                 "idp.assemble_form", "moving", {"form_id": "COA-1"}, "moving.assemble",
                 ("PII", "FTI")),
        StepSpec("open_311", "service_request", "311", "02-forms-idp",
                 "crm311.create_service_request", "moving", {"type": "Address Change"},
                 "moving.311", ("PII",), compensate_tool="crm311.cancel_service_request"),
        StepSpec("book_appt", "appointment", "City Clerk", "01-resident-services-311",
                 "scheduling.book_appointment", "moving", {"service": "address_verification"},
                 "moving.appt", ("PII",), compensate_tool="scheduling.cancel_appointment"),
    ],
    "job_loss": [
        StepSpec("assemble_ui", "form", "Shared Services", "02-forms-idp",
                 "idp.assemble_form", "job_loss", {"form_id": "UI-APP"}, "jobloss.assemble",
                 ("PII", "FTI")),
        StepSpec("create_benefits", "benefits", "HHS", "04-benefits-caseworker",
                 "eligibility.create_application", "job_loss", {"program": "UI"},
                 "jobloss.app", ("PII", "PHI", "FTI"),
                 compensate_tool="eligibility.withdraw_application"),
        StepSpec("rfi_notice", "benefits", "HHS", "04-benefits-caseworker",
                 "eligibility.generate_notice", "job_loss", {"type": "Request for Information"},
                 "jobloss.notice", ("PII", "PHI")),
    ],
    "disaster": [
        StepSpec("report_damage", "service_request", "311", "02-forms-idp",
                 "crm311.create_service_request", "disaster", {"type": "Disaster Damage Report"},
                 "disaster.311", ("PII",), compensate_tool="crm311.cancel_service_request"),
        StepSpec("assemble_assistance", "form", "Shared Services", "02-forms-idp",
                 "idp.assemble_form", "disaster", {"form_id": "DIS-ASSIST"}, "disaster.assemble",
                 ("PII", "FTI")),
        StepSpec("create_assistance", "benefits", "HHS", "04-benefits-caseworker",
                 "eligibility.create_application", "disaster", {"program": "Disaster Assistance"},
                 "disaster.app", ("PII", "PHI", "FTI"),
                 compensate_tool="eligibility.withdraw_application"),
    ],
    "bereavement": [
        StepSpec("assemble_estate", "form", "Shared Services", "02-forms-idp",
                 "idp.assemble_form", "bereavement", {"form_id": "ESTATE-1"}, "berv.assemble",
                 ("PII", "FTI")),
        StepSpec("death_record", "records_request", "Records", "05-public-records-foia",
                 "records.assemble_package", "bereavement", {"record_type": "Death Certificate"},
                 "berv.records", ("PII",), compensate_tool="records.void_package"),
        StepSpec("survivor_benefits", "benefits", "HHS", "04-benefits-caseworker",
                 "eligibility.create_application", "bereavement", {"program": "Survivor Benefits"},
                 "berv.benefits", ("PII", "PHI", "FTI"),
                 compensate_tool="eligibility.withdraw_application"),
    ],
    "new_business": [
        StepSpec("assemble_reg", "form", "Shared Services", "02-forms-idp",
                 "idp.assemble_form", "new_business", {"form_id": "BIZ-REG"}, "biz.assemble",
                 ("PII", "FTI")),
        StepSpec("create_permit", "permit", "Permitting", "03-permitting-licensing",
                 "permitting.create_application", "new_business", {"type": "Business"},
                 "biz.permit", ("PII",), compensate_tool="permitting.withdraw_application"),
    ],
}


def _forward(govgw, spec: StepSpec, approval: Dict[str, Any]):
    def fn(claims: Dict[str, Any], payload: Dict[str, Any]):
        res = govgw.invoke(user_claims=claims, agent_id=spec.agent_id, tool=spec.tool,
                           purpose=spec.purpose, args=spec.args, approval=approval,
                           idempotency_key=spec.idempotency_key)
        if not res.allowed:
            raise RuntimeError(f"governed write denied: {res.reason}")
        return res.result
    return fn


def _compensate(spec: StepSpec):
    def fn(claims: Dict[str, Any], payload: Dict[str, Any]):
        # Real deployment calls spec.compensate_tool (the agency's cancel/withdraw
        # API) through the gateway. Here we record the intended rollback so the
        # compliance trail is complete even when the fixture lacks a cancel method.
        payload.setdefault("_rollbacks", []).append(spec.compensate_tool or f"(no-op:{spec.name})")
    return fn


def build_saga(event: str, govgw, resident_ref: str, approval: Dict[str, Any]) -> Saga:
    specs = LIFE_EVENT_TEMPLATES.get(event)
    if not specs:
        raise ValueError(f"unknown life event {event!r}")
    steps = [SagaStep(name=s.name, intent=s.intent, agency=s.agency,
                      forward=_forward(govgw, s, approval),
                      compensate=_compensate(s) if s.compensate_tool else None,
                      material=s.material, idempotency_key=s.idempotency_key,
                      data_classes=list(s.data_classes)) for s in specs]
    return Saga(name=event, resident_ref=resident_ref, steps=steps)
