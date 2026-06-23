# SLG AI Agent Suite
### Governed AI Agents for State & Local Government — Built on AWS

> **The agent is not the product. The governance that makes it deployable, auditable, and compliant in a regulated government environment is.**

A field-ready accelerator of **8 governed SLG AI agents** — each deployable **standalone** with its own complete secure AWS architecture — plus an **optional Whole-of-Government orchestration platform** that coordinates them across agencies. **179 automated tests pass with no API key.** Grounded in current AWS and SLG sources (`SOURCES.md`, `decks/DECK-SOURCES.md`).

---

## 1. The need — what state & local government actually faces
AI is **NASCIO's #1 state-CIO priority for 2026**, yet **90% of states are stuck in pilots and only 25% have dedicated GenAI funding** (NASCIO). Residents experience government as fragmentation; agencies experience AI as ungoverned sprawl — a chatbot per agency, each a separate integration, security review, and audit. **The blocker is not the model.** It is identity, authorization, audit, data-class isolation, accessibility, and *which agency has the authority to act*.

The pain is specific, documented, and expensive:

| Workflow | The pain today (cited) |
|---|---|
| Public records / FOIA | National backlog **267,056 requests (+33%)**, **$723.4M** government-wide cost (DOJ OIP, FY2024) |
| Benefits / HHS | **69%** of Medicaid "unwinding" disenrollments were **procedural**, not ineligibility (KFF); benefits call centers **25-min waits, 29% abandonment** (CMS) |
| Permitting | Permitting friction ≈ **one-third** of the home price-vs-cost gap (Soltas & Gruber, MIT/Princeton, 2026) |
| Case intake / forms | A single complex intake took **45+ minutes** to summarize and route (Anne Arundel County) |
| IT service desk | A live contact costs **~$8** vs **~$0.10** self-service; only **9%** of people self-resolve today (Gartner) |
| Resident services | Residents navigate **dozens of departments** with no single front door |

---

## 2. How this solves it
**8 governed agents**, each a runnable workflow (intake → classify → gather evidence → draft → compliance check → **human gate** → finalize), every system touch flowing through a deny-by-default authorization gateway:

| # | Agent | What it does | Documented gain (cited; vendor-reported where noted) |
|---|---|---|---|
| **01** | Resident Services & 311 | Right service, cited answers, gated 311 actions | **−35%** call volume / **50%** faster (Grupo TX); **−4,000 calls/mo** (Indiana) |
| **02** | Forms & Document Processing | Extract, validate, assemble official forms | **45 min → <20s** (Anne Arundel); **49%** auto-approved (Arizona) |
| **03** | Permitting & Licensing | Requirements, prefill, parallel routing | **−70%** residential plan-review time (Honolulu) |
| **04** | Benefits / HHS Caseworker | Prescreen, evidence, notices | Appeal decision **3 hrs → 5 min** (Nevada DETR); backlog **40k → <5k** |
| **05** | Public Records / FOIA | Search, classify, propose redactions, package | Redaction **−98%**, files **32× faster** (HSI lab) |
| **06** | Procurement & Grants | Draft solicitations, organize bid evidence | **−50%** internal review cycle; **−17%** RFP completion |
| **07** | GovOps IT Service Desk | Triage, tickets, runbooks, modernization | **75%** queries self-resolved (IBM); **−50–70%** MTTR (ServiceNow) |
| **08** | Public Safety / Public Health | Summaries, reports, validated surveillance | Cooling-tower ID **−98%** (CDC, *peer-reviewed*); report time **−61%** (Leon County) |

> Numbers are documented results from named deployments and published benchmarks; vendor-reported figures are labeled, and the public-safety deck carries the peer-reviewed **null-result RCT** on-slide for honesty. Full citations: `decks/DECK-SOURCES.md`.

**The five controls that make it deployable** (this is the product):
1. **Deny-by-default gateway, least-privilege intersection** — `permitted ⇔ agent grant ∩ user entitlement`; the agent can never exceed the employee it acts for.
2. **Consequential actions withheld in code** — issue-permit / adjudicate / release-records / award are *absent from the agent's grants*, enforced by a passing test. A human owns them.
3. **Framework-enforced human gate** — `interrupt_before` / Step Functions `waitForTaskToken`; no code path commits without approval.
4. **Tamper-evident audit + WORM** — append-only DynamoDB + S3 Object Lock; PII/CJI/FTI masked at every boundary.
5. **In-account inference** — Amazon Bedrock via VPC endpoint + mandatory Guardrails; constituent data never leaves the VPC.

Plus the **Whole-of-Government Orchestration Platform** (`gov_platform/wog_orchestration/`) — see `ENTERPRISE-PLATFORM.md` — and five documented future use cases (`docs/FUTURE-USE-CASES.md`).

---

## 3. How it satisfies the regulations & security architecture
**A complete AWS architecture, edge to data tier** (see any deck's architecture slide and `docs/SUITE-ARCHITECTURE.md`):

```
Residents/staff → CloudFront + AWS WAF (OWASP managed rules, rate-limit) + Shield
   → API Gateway/ALB · Amazon Cognito (federates agency IdP → short-lived JWT; API GW JWT authorizer)
   → Agent runtime (Step Functions + Lambda, or AgentCore Runtime) in a private subnet
   → MCP authorization gateway (re-validates JWT + custom:slg_role claim; mints a scoped per-call token)
   → Amazon Bedrock (Claude) + Guardrails via VPC endpoint   [no PII egress]
   → DynamoDB append-only audit · S3 Object Lock (WORM) · KMS CMK per data class
Cross-cutting: CloudTrail · GuardDuty · Security Hub · Config · X-Ray · data-class isolation (CJI/FTI/PHI/EDU/public)
```

**Control → regime mapping** (full matrix: `docs/COMPLIANCE-CONTROL-MAPPINGS.md`, machine-readable in `governance/controls/control_mappings.py`):

| Regime | How it's addressed |
|---|---|
| **GovRAMP / FedRAMP** | Deploy on AWS authorized regions (GovCloud High / US Moderate) |
| **CJIS Security Policy v6.0** | CJI account/VPC isolation; deny-by-default gateway; scoped tokens; masked audit |
| **IRS Pub 1075 (FTI)** | FTI isolation + masking; KMS; access logging; WORM retention |
| **HIPAA / MARS-E → ARC-AMPE** | PHI masking; deterministic eligibility engine **outside** the LLM; least privilege |
| **FERPA / DPPA** | Security-trimmed retrieval; consent; driver's-license masking; purpose-bound scopes |
| **ADA Title II / WCAG 2.1 AA** | Accessibility checks on AI output in CI (deadlines Apr 2027 / Apr 2028) |
| **NIST AI RMF** | Grounding, prompt registry, evals, red team, fairness, HITL gates |
| **PCI DSS** | Card masking (Luhn); none in prompts/audit; tokenized payment connector |

Each control is marked **Implemented** (in the platform) vs **Configurable** (the customer wires their IdP, validates connectors, sets Guardrail policy and retention schedule, and owns ATO/GovRAMP and CSV for the intended use). The **CISO security-review checklist** is in `gtm/SELLER-SA-FIELD-GUIDE.md` §6.

---

## 4. How to position it
- **Standalone first, platform when ready.** One `scripts/deploy.sh <agent>` stands up a complete isolated stack (own VPC, CloudFront+WAF edge, Cognito JWT, KMS, WORM audit, gateway, agent) with **no WoG dependency** (`docs/DEPLOYMENT-MODELS.md`). Grow agent by agent; the WoG platform is additive.
- **Sellers & SAs start here:** `gtm/SELLER-SA-FIELD-GUIDE.md` (9-phase playbook: understand → qualify → position → pick the deck → discovery → CISO security-fit → SA deployment → commercialize) and the one-page `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md`.
- **Decks (one location, `decks/`):** 8 per-agent narrative decks + the WoG platform deck + a suite executive overview — each a 6-slide arc (hook → problem → governed solution pipeline → **true AWS architecture & traffic-flow diagram** → tradeoffs/results) with a full **TIMING + talk-track in the speaker notes** and grounded, cited figures.
- **Pitch narrative & objection handling:** `gtm/WOG-PLATFORM-GTM-STORY.md`.

---

## The eight agents (detail)
Each agent ships: a runnable workflow (per-intent action mapping), gateway-backed tools, a test suite, a README + four-document set, **a step-by-step AWS deploy runbook** (`<agent>/docs/DEPLOY-RUNBOOK.md`), a customer deck (`decks/`), and an AWS-native Strands/Step Functions rebuild. Deliberate omissions are a feature — the legally consequential commit actions are withheld from the agents in code and verified by tests.

## Shared platform (`platform_core/slg_agent_platform/`)
MCP authorization gateway (deny-by-default, least-privilege intersection, HITL gate, scoped tokens, PII/CJI/FTI-masked append-only audit) · the masker · LLM factory (in-account Bedrock + Guardrails) · connector framework (fixture/live) · A2A supervisor.

## Governance & evaluation (`governance/`)
Grounding verification · prompt registry (hash-pinned, drift-failing CI) · eval harness · red team · fairness (four-fifths) · **accessibility (WCAG/ADA Title II)** · compliance control mappings · HITL-enforced tests. All run with no API key.

## Whole-of-Government Orchestration (`gov_platform/wog_orchestration/`)
Govern-tool-access contract · canonical data + adapters · AAL-gated consent ledger · durable **saga with compensation** · compliance event bus + evidence · **5 life-events live** (moving, job_loss, new_business, disaster, bereavement). Runnable: `aws-native-reference/wog-platform/local_runner.py`. The platform story: `ENTERPRISE-PLATFORM.md`.

## Deployment models — standalone first, platform when ready
Every agent deploys **standalone** (`network.yaml` own VPC + Flow Logs + Bedrock endpoint · `edge.yaml` CloudFront + WAF + Shield · `security.yaml` KMS + Guardrail + Cognito · `data.yaml` append-only audit + S3 Object Lock WORM · gateway · agent) with **no WoG dependency**. Adopt the WoG orchestration layer later, agent by agent; the same agents become saga steps unchanged. CloudFormation + Terraform, commercial **and** GovCloud. See `docs/DEPLOYMENT-MODELS.md`.

## Go-to-market & deploy assets
`gtm/SELLER-SA-FIELD-GUIDE.md` (seller/SA playbook) · `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md` (one-pager) · `gtm/WOG-PLATFORM-GTM-STORY.md` (pitch narrative, personas, objection Q&A, TCO framework) · `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` (16-stage architect deploy) · per-agent `docs/DEPLOY-RUNBOOK.md` · ops runbooks (`runbooks/`: incident, DR, model-degradation, HITL queue) · decks (`decks/`).

## Quick start
```bash
pip install -e platform_core
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance gov_platform/wog_orchestration/tests -q   # green, no API key
cd 01-resident-services-311 && EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py   # 5 life-events + a rollback
```

## Compliance disclaimer
A **decision-support accelerator** for qualified government staff — not a certified system, an ATO, or an approved adjudication tool. AI-generated content requires human review before any consequential action; the AI never takes irreversible action autonomously. Customers own ATO/GovRAMP, IdP integration, connector validation, Guardrail configuration, retention schedule, and CSV for the intended use.
