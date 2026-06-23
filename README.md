# SLG AI Agent Suite
### Governed AI Agents for State & Local Government — Built on AWS

> **The agents are not the product. The governed platform that makes them deployable, auditable, and compliant in a regulated government environment is.**

A systems integrator deploying AI for a state agency, county, or city cannot hand a customer a collection of LLM calls and call it done. Every action an agent touches — a 311 case, a permit packet, a benefits application, a public-records release, a contract award — carries privacy, civil-rights, records-retention, and accountability obligations that exist before the first line of agent code is written. This suite embeds those controls from the first commit: **deny-by-default authorization with least-privilege intersection, PII/CJI/FTI masking, grounding verification, accessibility (ADA Title II / WCAG) checks, a framework-enforced human-approval gate, and a tamper-evident audit trail** with WORM retention.

The result is a deployable accelerator — not a certified product — that gives an engagement team a credible, compliant starting point across the highest-value SLG workflows, plus the **Whole-of-Government Orchestration Platform** the agents compose into.

**Status:** platform core + governance + WoG orchestration (5 life-events, runnable saga) + **all 8 agents** built to flagship depth · AWS-native rebuilds (Strands + Step Functions) · CloudFormation + Terraform IaC with **commercial *and* GovCloud** parity · **179 automated tests passing with no API key** · GTM story + architect deployment runbook · grounded in current AWS + SLG sources (`SOURCES.md`).

---

## The Eight Agents
| # | Agent | Problem it solves | Key systems | Key obligations |
|---|---|---|---|---|
| **01** | Resident Services & 311 Navigator | Residents can't find the right agency across hundreds of pages/PDFs | 311/CRM, KB, Identity, Scheduling, GIS | ADA Title II, state privacy, no-disclosure-without-auth |
| **02** | Forms & Intelligent Document Processing | Re-keying, missing fields, classification of attachments | IDP, KB, Identity, Consent | IRS 1075, HIPAA, DPPA |
| **03** | Permitting & Licensing | Multi-department reviews; applicants can't see what's missing | Permitting (Accela/Tyler), GIS, IDP | Issuance stays with a human official |
| **04** | Benefits / HHS Caseworker Assist | Complex rules, repeated evidence, caseworker system-switching | Eligibility, IDP, Identity | HIPAA/MARS-E→ARC-AMPE, IRS 1075; **deterministic engine + human adjudication** |
| **05** | Public Records / FOIA & Redaction | Search, dedup, exemptions, redaction, retention | Records/ECMS, KB | Public-records law; **release stays with a records officer** |
| **06** | Procurement, Contracting & Grants | Slow, document-heavy solicitations and grants | Procurement/ERP, IDP | **Award stays with a procurement officer** |
| **07** | GovOps IT Service Desk & Modernization | Legacy systems, workforce shortages, ticket volume | ITSM, KB | No destructive ops without approval |
| **08** | Public Safety / Public Health Case & Report | Narrative-heavy reports; surveillance queries | Incident systems, surveillance DB | CJIS/PHI separation; **no probable cause / enforcement by AI** |

Plus: the **Whole-of-Government Orchestration Platform** (`gov_platform/wog_orchestration/`) and five documented future use cases (`docs/FUTURE-USE-CASES.md`).

> **Deliberate omissions are a feature.** The legally consequential commit actions — issue a permit, adjudicate eligibility, release records, award a contract — are *withheld from the agents entirely* in `policy.py`. A human role holds them. This is verified by an automated test.

---

## Shared Platform (`platform_core/slg_agent_platform/`)
- **MCP Authorization Gateway** — the governed front door. Deny-by-default; `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]`. High-risk writes block until a verified human approval record exists. Short-lived scoped tokens, PII-masked append-only audit. Reference logic for **Bedrock AgentCore Gateway + Identity**; tool names map 1:1 to gateway targets.
- **PII/CJI/FTI Masker** — SSN, driver's license (DPPA), FTI/EIN, case IDs, addresses, cards (Luhn). Runs at every log/audit boundary.
- **LLM Factory** — Anthropic API or in-account **Amazon Bedrock** (no PII egress) with **Bedrock Guardrails**; demo mode bypasses the LLM.
- **Connector Framework** — one interface, fixture (offline/CI) + live (REST/agency adapters); identical signatures.
- **A2A Supervisor** — holds no tool grants; routes intents to specialists who each still pass the gateway.

## Governance & Evaluation (`governance/`)
Grounding verification · prompt registry (hash-pinned, drift-failing CI) · structural eval harness · red team (injection, exfiltration, authz bypass) · fairness (four-fifths) · **accessibility (WCAG/ADA Title II)** · compliance control mappings · HITL-enforced tests. All run with **no API key**.

## Whole-of-Government Orchestration (`gov_platform/wog_orchestration/`)
Canonical data layer · consent + identity-assurance ledger (NIST 800-63 AAL) · compliance event bus · life-event orchestrator with **explicit resident confirmation before every material action**.

---

## Quick start
```bash
pip install -e platform_core
PYTHONPATH=platform_core:. python -m pytest platform_core governance gov_platform 01-resident-services-311 aws-native-reference -q
cd 01-resident-services-311 && EXTRACT_MODE=demo python demo/demo_run.py
```

## AWS deployment
`infra/cloudformation/quickstart.yaml` (master) + Terraform parity (`infra/terraform/`), both commercial and **GovCloud** (`infra/terraform/govcloud/`). Two gateway paths (`portable` API Gateway+Cognito for any region incl. GovCloud, or `agentcore`), two run modes (`native` Step Functions+Lambda, or `container` ECS/AgentCore Runtime). See `docs/` and `SOURCES.md`.

## Go-to-market & deploy assets
`gtm/WOG-PLATFORM-GTM-STORY.md` (pitch narrative, personas, objection-handling Q&A, scalability, cost, regulatory alignment) · `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` (16-stage architect deploy: prerequisites → networking → KMS/Cognito → Bedrock + Guardrails → knowledge base → gateway → agents → WoG saga → HITL → audit/WORM → accessibility → smoke tests → go-live) · three decks (Agent 01 customer, suite executive, WoG platform).

## Compliance disclaimer
A **decision-support accelerator** for qualified government staff — not a certified system, an ATO, or an approved adjudication tool. AI-generated content requires human review before any consequential action. The AI never takes irreversible action autonomously. Customers own ATO/GovRAMP, IdP integration, connector validation, Guardrail configuration, and change control.
