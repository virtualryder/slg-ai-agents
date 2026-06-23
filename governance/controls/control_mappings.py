"""
Compliance control mappings — which platform control satisfies which obligation.

Each entry ties an SLG regulatory regime to the concrete platform/AWS control
that addresses it, plus the maturity (Implemented / Configurable / Customer).
A CISO or auditor reads this to see why the architecture is defensible; a
solution architect reads it to know what they must still configure per customer.
Authoritative sources are tracked in SOURCES.md at the repo root.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ControlMapping:
    regime: str
    obligation: str
    platform_control: str
    aws_service: str
    status: str  # Implemented | Configurable | Customer


MAPPINGS: List[ControlMapping] = [
    ControlMapping("GovRAMP (StateRAMP)", "Verified cloud security baseline (Moderate/High)",
                   "Deploy on AWS authorized regions; inherit AWS authorization",
                   "AWS GovCloud (US) High / US East-West Moderate", "Configurable"),
    ControlMapping("FBI CJIS Security Policy v6.0", "Protect Criminal Justice Information; segregation",
                   "Separate CJI account/VPC boundary; deny-by-default gateway; scoped tokens; audit",
                   "Organizations + VPC + KMS CMK + CloudTrail", "Configurable"),
    ControlMapping("IRS Publication 1075", "Safeguard Federal Tax Information (FTI)",
                   "FTI data class isolation; PII/FTI masking at audit boundary; encryption; access logging",
                   "KMS + S3 Object Lock + DynamoDB append-only + CloudTrail", "Configurable"),
    ControlMapping("HIPAA / CMS (MARS-E → ARC-AMPE)", "Protect PHI in Medicaid/exchange eligibility",
                   "PHI masking; least-privilege gateway; deterministic eligibility engine outside LLM",
                   "Bedrock (BAA-eligible) + Guardrails + KMS", "Configurable"),
    ControlMapping("FERPA", "Protect student education records",
                   "Security-trimmed retrieval; consent checks; access logging",
                   "Q Business / Knowledge Bases ACL propagation + CloudTrail", "Configurable"),
    ControlMapping("DPPA (18 U.S.C. 2721)", "Restrict use of DMV personal information",
                   "DL/ID masking; purpose-bound tool scopes; consent.record",
                   "Gateway policy + KMS + audit", "Implemented"),
    ControlMapping("ADA Title II / WCAG 2.1 AA", "Accessible web/mobile (AI output in scope)",
                   "Accessibility pre-flight on generated content (alt text, heading order, link text, plain language)",
                   "governance/accessibility + CI (axe-core)", "Implemented"),
    ControlMapping("NIST AI RMF 1.0", "Govern/Map/Measure/Manage AI risk",
                   "Grounding verification; prompt registry; evals; red team; fairness; HITL gates",
                   "governance/* + CloudWatch", "Implemented"),
    ControlMapping("State public-records / retention", "Retention, legal hold, auditability of records & AI traces",
                   "Append-only audit; WORM finalized snapshots; retention config; prompt/trace capture",
                   "DynamoDB (deny Update/Delete) + S3 Object Lock COMPLIANCE", "Configurable"),
    ControlMapping("PCI DSS (fee/utility payments)", "Protect cardholder data",
                   "Card masking (Luhn); no card data in prompts/audit; tokenized payment connector",
                   "Gateway + masker + payment provider", "Configurable"),
]


def by_regime(regime: str) -> List[ControlMapping]:
    return [m for m in MAPPINGS if m.regime.lower().startswith(regime.lower())]
