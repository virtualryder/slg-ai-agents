# Forms & Intelligent Document Processing — Compliance & Security Mapping

Full matrix: `governance/controls/control_mappings.py`; sources: repo-root `SOURCES.md`.

| Concern | Control in this agent | AWS service |
|---|---|---|
| Least privilege | deny-by-default gateway: agent grant ∩ user entitlement | AgentCore Gateway/Identity or API GW + STS |
| Human owns consequential action | `interrupt_before=[human_review_gate]`; high-risk writes blocked without approval | Step Functions `waitForTaskToken` |
| No fabricated facts | `governance/grounding.py` in `compliance_check` + CI | deterministic (no API key) |
| Accessibility (ADA Title II / WCAG 2.1 AA) | `governance/accessibility/wcag.py` on output | CI (axe-core) |
| PII/CJI/FTI never in logs/audit | `slg_agent_platform/pii.py` at every audit boundary | KMS, masked DynamoDB |
| Records retention | append-only audit + WORM snapshots | DynamoDB (deny Update/Delete) + S3 Object Lock |

**Domain guard.** The agent must not infer or fabricate a legally significant fact (income, identity, dates) the applicant did not supply — it may only identify a missing item.

**Key obligations:** IRS Pub 1075 (FTI), HIPAA, DPPA, state privacy.
