# Benefits / HHS Caseworker Assist — Compliance & Security Mapping

Full matrix: `governance/controls/control_mappings.py`; sources: repo-root `SOURCES.md`.

| Concern | Control in this agent | AWS service |
|---|---|---|
| Least privilege | deny-by-default gateway: agent grant ∩ user entitlement | AgentCore Gateway/Identity or API GW + STS |
| Human owns consequential action | `interrupt_before=[human_review_gate]`; high-risk writes blocked without approval | Step Functions `waitForTaskToken` |
| Consequential action withheld | `eligibility.adjudicate` absent from the agent in `policy.py` (human-only); verified by test | Step Functions `waitForTaskToken` |\n| No fabricated facts | `governance/grounding.py` in `compliance_check` + CI | deterministic (no API key) |
| Accessibility (ADA Title II / WCAG 2.1 AA) | `governance/accessibility/wcag.py` on output | CI (axe-core) |
| PII/CJI/FTI never in logs/audit | `slg_agent_platform/pii.py` at every audit boundary | KMS, masked DynamoDB |
| Records retention | append-only audit + WORM snapshots | DynamoDB (deny Update/Delete) + S3 Object Lock |

**Domain guard.** Eligibility determination runs in a deterministic rules engine OUTSIDE the LLM. The agent prescreens (nonbinding), organizes evidence and drafts notices; it never adjudicates, denies, or terminates a benefit.

**Key obligations:** HIPAA / MARS-E→ARC-AMPE, IRS Pub 1075, SSA data-exchange, program rules.
