# SLG AI Agent Suite
### Governed AI Agents for State & Local Government — Built on AWS

> **The agent is not the product. The governance that makes it deployable, auditable, and compliant in a regulated government environment is.**

A field-ready accelerator of **8 governed SLG AI agents** — each deployable **standalone** with its own complete secure AWS architecture — plus an **optional Whole-of-Government orchestration platform** that coordinates them across agencies. **179 automated tests pass with no API key.** Grounded in current AWS and SLG sources (`SOURCES.md`, `decks/DECK-SOURCES.md`).

> **Reviewing this for production?** Start with §5 and `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` — an honest gap assessment + a RACI shared-responsibility matrix. This is a **production-shaped accelerator, not an authorized, production-ready system**; live connectors, ATO/GovRAMP, and security testing are engagement work.

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
Residents/staff -> CloudFront + AWS WAF (OWASP managed rules, rate-limit) + Shield
   -> API Gateway/ALB . Amazon Cognito (federates agency IdP -> short-lived JWT; API GW JWT authorizer)
   -> Agent runtime (Step Functions + Lambda, or AgentCore Runtime) in a private subnet
   -> MCP authorization gateway (re-validates JWT + custom:slg_role claim; mints a scoped per-call token)
   -> Amazon Bedrock (Claude) + Guardrails via VPC endpoint   [no PII egress]
   -> DynamoDB append-only audit . S3 Object Lock (WORM) . KMS CMK per data class
Cross-cutting: CloudTrail . GuardDuty . Security Hub . Config . X-Ray . data-class isolation (CJI/FTI/PHI/EDU/public)
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

Each control is marked **Implemented** (in the platform) vs **Configurable** (the customer wires their IdP, validates connectors, sets Guardrail policy and retention schedule, and owns ATO/GovRAMP and CSV for the intended use). The **CISO security-review checklist** is in `gtm/SELLER-SA-FIELD-GUIDE.md` §6, and the full ownership split is in §5 below.

---

## 4. How to position it
- **Standalone first, platform when ready.** One `scripts/deploy.sh <agent>` stands up a complete isolated stack (own VPC, CloudFront+WAF edge, Cognito JWT, KMS, WORM audit, gateway, agent) with **no WoG dependency** (`docs/DEPLOYMENT-MODELS.md`). Grow agent by agent; the WoG platform is additive.
- **Sellers & SAs start here:** `gtm/SELLER-SA-FIELD-GUIDE.md` (9-phase playbook) and the one-page `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md`.
- **Decks (one location, `decks/`):** 8 per-agent narrative decks + the WoG platform deck + a suite executive overview — each a 6-slide arc (hook → problem → governed solution pipeline → **true AWS architecture & traffic-flow diagram** → tradeoffs/results) with a full **TIMING + talk-track in the speaker notes** and grounded, cited figures.
- **Pitch narrative & objection handling:** `gtm/WOG-PLATFORM-GTM-STORY.md`.

---

## 5. Production readiness — and who owns what (read before any production decision)
**Honest status: this is a production-shaped accelerator, not an authorized, production-ready system — and it doesn't claim to be.** That honesty is the point: it embeds the governance controls usually retrofitted, which de-risks the path to production, but real work remains and most of it is the customer's.

**Why it gives confidence (verifiable today):** consequential actions withheld in code + tested · framework-enforced human gate · deny-by-default least-privilege · WORM audit + masking · complete AWS security architecture mapped to your regimes · no lock-in (readable Python, CFN + Terraform) · 179 tests passing.

**What still must be built/authorized before go-live (stated plainly):**
- **Integrations are fixtures** — there are **no live connectors** yet to 311/CRM, eligibility systems, Accela/Tyler, ECMS, ServiceNow, etc. Each must be built and validated (usually the largest line item).
- **No ATO / GovRAMP authorization** and **no third-party security testing** (pen test, threat model). The Python gateway is a *reference model* of the authorization; the production AgentCore Gateway / API Gateway + Cedar authorizer must be tested, not just the analog.
- **Model-risk validation**, Guardrail/red-team tuning against your data, accessibility (axe-core + manual), DR game day, IdP integration, retention schedule, and **HITL queue staffing** are customer-owned engagement work.

**Who owns what (RACI summary — AWS · Delivery Partner · Customer):** AWS owns the authorized cloud; the **Delivery Partner** builds connectors, configures, tests, and extends; the **Customer (agency)** owns data classification, IdP, ATO/GovRAMP, model-risk validation, retention, and day-2 operations.

> **Full detail:** `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` — the gap assessment, the 24-row shared-responsibility (RACI) matrix, a gated go-live checklist, and a phased path (start with a low-blast-radius agent like Resident Services or IT service desk; **not** Benefits or Public Safety first).

---

## What this is — and what it is not
| This is | This is not |
|---|---|
| A governed, auditable **accelerator** with the hard controls built in | A certified, validated, ATO'd SaaS product you deploy unchanged |
| A reference architecture + IaC you deploy into your account and **own** | A black-box dependency or a turnkey integration |
| Decision-support — drafts, assembles, routes, flags — humans decide | Autonomous decisioning in regulated workflows |
| Demonstrated + deployable-by-design (179 tests, no API key) | Production-ready until the go-live checklist is met |

## Repository map
```
README.md  ENTERPRISE-PLATFORM.md  SUITE-STATUS.md  SOURCES.md  IMPROVEMENTS-OVER-EDU-HCLS.md
01-resident-services-311/ ... 08-public-safety-health/   # 8 agents (code, tests, docs, deploy runbook)
platform_core/slg_agent_platform/                        # gateway, masker, LLM factory, connectors, A2A
gov_platform/wog_orchestration/                          # Whole-of-Government: govern, canonical, consent, saga, events
governance/                                              # grounding, prompts, evals, red team, fairness, accessibility, controls
aws-native-reference/                                    # Strands + Step Functions rebuilds (per agent + WoG saga)
infra/cloudformation/  infra/terraform/                  # IaC: edge, network, security, data, gateway, agent, wog-platform (commercial + GovCloud)
docs/                                                    # architecture, compliance mappings, deployment models, PRODUCTION-READINESS, why-the-MCP-layer
gtm/                                                     # seller/SA field guide, first-meeting cheat-sheet, WoG GTM story
decks/                                                   # 10 customer decks (talk track in speaker notes) + DECK-SOURCES.md
runbooks/                                                # deploy (platform), incident, DR, model-degradation, HITL queue
```

## The eight agents (detail)
Each agent ships: a runnable workflow (per-intent action mapping), gateway-backed tools, a test suite, a README + four-document set, **a step-by-step AWS deploy runbook** (`<agent>/docs/DEPLOY-RUNBOOK.md`), a customer deck (`decks/`), and an AWS-native Strands/Step Functions rebuild. Deliberate omissions are a feature — the legally consequential commit actions are withheld from the agents in code and verified by tests.

## Shared platform (`platform_core/slg_agent_platform/`)
MCP authorization gateway (deny-by-default, least-privilege intersection, HITL gate, scoped tokens, PII/CJI/FTI-masked append-only audit) · the masker · LLM factory (in-account Bedrock + Guardrails) · connector framework (fixture/live) · A2A supervisor.

## Governance & evaluation (`governance/`)
Grounding verification · prompt registry (hash-pinned, drift-failing CI) · eval harness · red team · fairness (four-fifths) · **accessibility (WCAG/ADA Title II)** · compliance control mappings · HITL-enforced tests. All run with no API key.

## Whole-of-Government Orchestration (`gov_platform/wog_orchestration/`)
Govern-tool-access contract · canonical data + adapters · AAL-gated consent ledger · durable **saga with compensation** · compliance event bus + evidence · **5 life-events live** (moving, job_loss, new_business, disaster, bereavement). Runnable: `aws-native-reference/wog-platform/local_runner.py`. The platform story: `ENTERPRISE-PLATFORM.md`.

## Deployment models — standalone first, platform when ready
Every agent deploys **standalone** (`edge.yaml` CloudFront + WAF + Shield · `network.yaml` own VPC + Flow Logs + Bedrock endpoint · `security.yaml` KMS + Guardrail + Cognito · `data.yaml` append-only audit + S3 Object Lock WORM · gateway · agent) with **no WoG dependency**. Adopt the WoG orchestration layer later, agent by agent; the same agents become saga steps unchanged. CloudFormation + Terraform, commercial **and** GovCloud. See `docs/DEPLOYMENT-MODELS.md`.

## Go-to-market & deploy assets
`gtm/SELLER-SA-FIELD-GUIDE.md` (seller/SA playbook) · `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md` (one-pager) · `gtm/WOG-PLATFORM-GTM-STORY.md` (pitch, personas, objection Q&A) · `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` (gap assessment + RACI) · `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` (16-stage architect deploy) · per-agent `docs/DEPLOY-RUNBOOK.md` · ops runbooks · decks (`decks/`).

## Quick start
```bash
pip install -e platform_core
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance gov_platform/wog_orchestration/tests -q   # green, no API key
cd 01-resident-services-311 && EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py   # 5 life-events + a rollback
```

## Compliance disclaimer
A **decision-support accelerator** for qualified government staff — not a certified system, an ATO, or an approved adjudication tool. AI-generated content requires human review before any consequential action; the AI never takes irreversible action autonomously. Customers own ATO/GovRAMP, IdP integration, connector validation, Guardrail configuration, retention schedule, and CSV for the intended use. See `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
