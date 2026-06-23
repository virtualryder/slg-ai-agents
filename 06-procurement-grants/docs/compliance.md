# Procurement, Contracting & Grants — Compliance & Security Mapping

Full matrix: `governance/controls/control_mappings.py`; sources: repo-root `SOURCES.md`.

| Concern | Control in this agent | AWS service |
|---|---|---|
| Least privilege | deny-by-default gateway: agent grant ∩ user entitlement | AgentCore Gateway/Identity or API GW + STS |
| Human owns consequential action | `interrupt_before=[human_review_gate]`; high-risk writes blocked without approval | Step Functions `waitForTaskToken` |
| Consequential action withheld | `procurement.award` absent from the agent in `policy.py` (human-only); verified by test | Step Functions `waitForTaskToken` |\n| No fabricated facts | `governance/grounding.py` in `compliance_check` + CI | deterministic (no API key) |
| Accessibility (ADA Title II / WCAG 2.1 AA) | `governance/accessibility/wcag.py` on output | CI (axe-core) |
| PII/CJI/FTI never in logs/audit | `slg_agent_platform/pii.py` at every audit boundary | KMS, masked DynamoDB |
| Records retention | append-only audit + WORM snapshots | DynamoDB (deny Update/Delete) + S3 Object Lock |

**Domain guard.** The agent organizes evidence and applies a deterministic, published scoring rubric; it must NOT select a winning bidder or alter evaluation criteria — the procurement officer owns the legally consequential award.

**Key obligations:** procurement law, required clauses, grant terms, immutable evaluation record.
