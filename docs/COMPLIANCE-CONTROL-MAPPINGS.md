# Compliance Control Mappings (SLG)
Machine-readable in `governance/controls/control_mappings.py`. Sources: `../SOURCES.md`.

| Regime | Obligation | Platform control | AWS service | Status |
|---|---|---|---|---|
| GovRAMP (StateRAMP) | Verified cloud baseline | Deploy on authorized regions | GovCloud High / US Moderate | Configurable |
| CJIS Security Policy v6.0 | Protect CJI; segregation | CJI account/VPC boundary; deny-by-default gateway; scoped tokens; audit | Organizations + VPC + KMS + CloudTrail | Configurable |
| IRS Pub 1075 | Safeguard FTI | FTI isolation; FTI masking at audit boundary; encryption; access logging | KMS + S3 Object Lock + DynamoDB + CloudTrail | Configurable |
| HIPAA / MARS-E→ARC-AMPE | Protect PHI in Medicaid/exchange | PHI masking; least-privilege gateway; **deterministic eligibility engine outside LLM** | Bedrock (BAA) + Guardrails + KMS | Configurable |
| FERPA | Student records | Security-trimmed retrieval; consent; logging | Q Business/KB ACL propagation + CloudTrail | Configurable |
| DPPA | DMV personal info | DL/ID masking; purpose-bound scopes; consent.record | Gateway policy + KMS + audit | Implemented |
| ADA Title II / WCAG 2.1 AA | Accessible web/mobile incl. AI output | Accessibility pre-flight (alt/heading/link/plain-language) | governance/accessibility + CI | Implemented |
| NIST AI RMF 1.0 | Govern/Map/Measure/Manage | Grounding; prompt registry; evals; red team; fairness; HITL | governance/* + CloudWatch | Implemented |
| Public-records / retention | Retention, legal hold, AI-trace auditability | Append-only audit; WORM snapshots; trace capture | DynamoDB (deny Update/Delete) + S3 Object Lock | Configurable |
| PCI DSS | Cardholder data | Card masking (Luhn); none in prompts/audit; tokenized payments | Gateway + masker + payment provider | Configurable |

**Two currency notes baked in:** ADA Title II deadlines are now **Apr 26, 2027 (≥50k pop.) / Apr 26, 2028 (smaller + special districts)** after DOJ's Apr 2026 extension; CMS **MARS-E is transitioning to ARC-AMPE** (Mar 4, 2026).
