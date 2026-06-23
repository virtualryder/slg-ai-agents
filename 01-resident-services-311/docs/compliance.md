# Agent 01 — Compliance & Security Mapping

The full machine-readable matrix is `governance/controls/control_mappings.py`; this is the
agent-specific view. Authoritative sources: repo-root `SOURCES.md`.

| Concern | Control in this agent | AWS service |
|---|---|---|
| No personal disclosure on name+address alone | `check_identity` node + gateway `identity.verify_resident`; compliance hard-fail | Cognito / IdP |
| Least privilege | deny-by-default gateway: agent grant ∩ user entitlement | AgentCore Gateway/Identity or API GW + STS |
| Human owns consequential action | `interrupt_before=[human_review_gate]`; high-risk writes blocked without approval record | Step Functions `waitForTaskToken` |
| No fabricated facts to residents | `governance/grounding.py` runs in `compliance_check` and CI | deterministic (no API key) |
| Accessibility (ADA Title II / WCAG 2.1 AA) | `governance/accessibility/wcag.py` on generated output | CI (axe-core) |
| PII/CJI/FTI never in logs/audit | `slg_agent_platform/pii.py` at every audit boundary | KMS, masked DynamoDB |
| Tamper-evident records retention | append-only audit + WORM snapshots | DynamoDB (deny Update/Delete) + S3 Object Lock |
| Data residency | in-account Bedrock inference, no PII egress | Bedrock + VPC endpoint + Guardrails |

**ADA note (current):** DOJ extended Title II web-rule deadlines one year (Apr 2026 IFR) —
entities ≥50,000 population: **Apr 26, 2027**; smaller/special districts: **Apr 26, 2028**.
AI-generated output is in scope.
