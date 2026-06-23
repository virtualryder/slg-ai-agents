# Public Safety / Public Health Case & Report — Compliance & Security Mapping

Full matrix: `governance/controls/control_mappings.py`; sources: `SOURCES.md`.

| Concern | Control | AWS service |
|---|---|---|
| Least privilege | deny-by-default gateway: agent grant ∩ user entitlement | AgentCore Gateway/Identity or API GW + STS |
| Human owns consequential action | `interrupt_before=[human_review_gate]`; high-risk writes blocked without approval | Step Functions `waitForTaskToken` |
| No fabricated facts | `governance/grounding.py` in `compliance_check` + CI | deterministic (no API key) |
| Accessibility (ADA Title II / WCAG 2.1 AA) | `governance/accessibility/wcag.py` on output | CI (axe-core) |
| PII/CJI/FTI never in logs/audit | `slg_agent_platform/pii.py` at every audit boundary | KMS, masked DynamoDB |
| Records retention | append-only audit + WORM snapshots | DynamoDB (deny Update/Delete) + S3 Object Lock |

**Domain guard.** AI must not independently establish probable cause, calculate dangerousness, recommend sentencing, make a medical diagnosis, or initiate enforcement. CJI, PHI and public data stay in separate environments; surveillance SQL is validated deterministically before execution.  **Key obligations:** FBI CJIS v6.0, HIPAA/PHI, public-records.
