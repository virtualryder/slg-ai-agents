"""
Shared runtime for the WoG saga Lambdas.

Each Lambda is a Step Functions Task body. They share one GovernedToolGateway,
ConsentLedger, and ComplianceEventBus per execution. In AWS these are backed by
DynamoDB (consent, event store) and EventBridge; here they are process objects
initialized by init() so the local Step Functions runner can drive the exact same
handlers end-to-end without AWS.
"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(_REPO / "platform_core"), str(_REPO)]

from gov_platform.wog_orchestration.consent import ConsentLedger          # noqa: E402
from gov_platform.wog_orchestration.events import ComplianceEventBus, ComplianceEvent  # noqa: E402
from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway  # noqa: E402

CONSENT: Optional[ConsentLedger] = None
BUS: Optional[ComplianceEventBus] = None
GOVGW: Optional[GovernedToolGateway] = None
IDEMPOTENCY = None


def init(consent: ConsentLedger, bus: ComplianceEventBus, govgw: GovernedToolGateway,
         idempotency=None) -> None:
    global CONSENT, BUS, GOVGW, IDEMPOTENCY
    CONSENT, BUS, GOVGW, IDEMPOTENCY = consent, bus, govgw, idempotency


def bootstrap() -> None:
    """Cold-start initializer. WOG_BACKEND=aws wires DynamoDB + EventBridge; else in-memory."""
    import os
    backend = os.getenv("WOG_BACKEND", "memory").strip().lower()
    if backend == "aws":
        from aws_backends import AwsConsentStore, AwsComplianceEventBus
        consent = AwsConsentStore(os.environ["CONSENT_TABLE"])
        bus = AwsComplianceEventBus(os.environ["EVENT_TABLE"], os.environ["EVENT_BUS_NAME"])
        idem_table = os.getenv("IDEMPOTENCY_TABLE")
        idem = None
        if idem_table:
            from aws_backends import AwsIdempotencyStore
            idem = AwsIdempotencyStore(idem_table)
    else:
        consent = ConsentLedger()
        bus = ComplianceEventBus()
        idem = None
    govgw = GovernedToolGateway(default_catalog(),
                                deployment_residency=os.getenv("DEPLOYMENT_RESIDENCY", "us"))
    init(consent, bus, govgw, idempotency=idem)
