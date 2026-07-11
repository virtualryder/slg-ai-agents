# Whole-of-Government Orchestration Platform — GTM Story & Talking Points
*A field asset for AWS account teams and SI sellers. Pair with `SLG-WoG-Orchestration-Platform-Deck.pptx` and the deployment runbook (`runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`).*

---

## 1. The story in one line
**Stop buying chatbots. Buy the governed substrate that turns AI into accountable digital government — one identity, one authorization model, one audit trail, shared across every agency.**

### 30-second version
"Every state and city is piloting AI, but they're piloting it agency by agency — a chatbot here, a form-filler there. Each one is a separate integration, a separate security review, a separate audit. The Whole-of-Government platform flips that: it's one governed layer — identity, authorization, audit, retention, accessibility — and the agents become configurations of it. A resident who moves, loses a job, or loses a loved one is served across agencies as one coordinated, consented, fully-audited transaction, with a human approving every consequential step. It runs on AWS, deploys in commercial or GovCloud, and the whole thing is runnable today with 179 automated governance tests."

### 2-minute version
Lead with the resident: *"A resident moves. Today they file a change of address with the DMV, separately update voter registration, separately start trash service, separately re-enroll a child in school — four agencies, four systems, four logins, and nobody has the whole picture."* Then the pivot: *"Our platform organizes services around that life event, not the org chart. A supervisor agent coordinates the agencies; a consent ledger makes sure nothing happens without the resident's permission at the right identity-assurance level; a durable saga executes the steps across agencies and — critically — rolls them back if one fails, so nobody is left half-enrolled; and every step lands in one immutable, retention-aware compliance record. The agents never hold cross-agency authority and never take a legally consequential action — a human owns the permit, the eligibility decision, the records release, the contract award. That's the difference between a science project and something a CISO will sign."*

---

## 2. The problem (the narrative that resonates)
- **Citizens experience government as fragmentation.** Hundreds of pages, dozens of agencies, repeated information, no single front door.
- **Agencies experience AI as sprawl.** NASCIO ranks AI the #1 state CIO priority for 2026, but 90% of states are still in pilots and only 25% have dedicated GenAI funding. The result is dozens of disconnected chatbots, each an ungoverned integration.
- **The real blocker is not the model.** It's identity, consent, interagency data-sharing, incompatible systems, and *which agency has the authority to act*. That is exactly what this platform governs.

> The punchline for an executive: *"The hard part of agentic government isn't the AI. It's proving who did what, on whose authority, to which record — and being able to undo it. We built that part."*

---

## 3. What the platform is (plain language, five pillars)
1. **Govern tool access** — every cross-agency action carries a contract: which agency, allowed purpose, data class, residency, transaction limit, idempotency, rollback, and a mandatory audit. No agent reaches a system of record any other way.
2. **Canonical data** — one definition of a resident, an address, a case; each agency maps its own system to that shared shape at the boundary.
3. **Workflow coordination** — a durable saga executes multi-agency transactions with consent + confirmation gates and automatic compensation (rollback) when a step fails.
4. **Compliance events** — every step (and every rollback) emits an immutable, PII-masked event; a case-level evidence package assembles automatically with retention set by data class.
5. **Identity & consent** — an assurance-gated (NIST 800-63 AAL), scoped, time-bound consent ledger; no cross-agency use without it.

The governing invariant: **the orchestrator holds no tool grants, and agents never commit the legally consequential action.** A human always does.

---

## 4. Why now
- **NASCIO 2026:** AI is the #1 state CIO priority (displacing cybersecurity).
- **The tooling is ready:** Amazon Bedrock AgentCore went GA (Oct 2025); it reached GovCloud (US-West) in May 2026; Bedrock + Guardrails + Knowledge Bases are FedRAMP High / DoD IL-4/5 in GovCloud.
- **The clock is real:** ADA Title II accessibility deadlines hit Apr 2027 (large) / Apr 2028 (smaller) and AI-generated output is in scope.
- **Peers are live:** Virginia Beach, Anne Arundel County, North Carolina, and 3,000+ counties via Kofile are already in production on AWS.

---

## 5. Who to pitch to (personas, hooks, proof)
| Persona | What they care about | The hook | The proof to show |
|---|---|---|---|
| **State CIO / CTO** | Moving from pilots to production; not 50 ungoverned bots | "One substrate, many agents — controls compound instead of multiplying audits" | The five pillars + 179 passing governance tests |
| **CISO / CISO's office** | Provable least privilege, audit, data-class isolation | "The agent can never exceed the employee, and the consequential action is withheld in code" | `policy.py` intersection + the withheld-action test + masked audit |
| **Chief Data / AI Officer** | Responsible-AI governance, NIST AI RMF | "Grounding, prompt registry, red team, fairness, accessibility — built in, not bolted on" | `governance/` + control mappings |
| **Director of Architecture / Enterprise Architect** | Reference architecture, IaC, no lock-in | "CloudFormation + Terraform, commercial & GovCloud, portable gateway path" | The deployment runbook + `infra/` |
| **Agency program directors** (HHS, Permitting, Records, Procurement) | Throughput, backlog, constituent experience | The agent for THEIR workflow + its ROI worksheet | The per-agent deck + demo |
| **Budget / CFO** | ROI, predictable cost, funding path | "Serverless, pay-per-use; pilot funded via AWS programs" | The TCO model below + MAP/funding |
| **Accessibility / ADA officer** | Title II compliance for AI output | "AI output is accessibility-tested in CI" | `governance/accessibility/` |

**Sequencing tip:** land with one agency program director (visible constituent win) + the CISO (governance comfort), then expand to the CIO/EA conversation about the platform.

---

## 6. Discovery questions (qualify + shape)
1. How many AI pilots are running across your agencies today, and who governs them?
2. When an agent touches a system of record, can you show an auditor who authorized it and undo it?
3. Which life events generate the most cross-agency friction for residents? (move, job loss, new business, disaster, bereavement)
4. What's your data-class landscape — CJI, FTI, PHI, education — and how is it isolated today?
5. Commercial regions or GovCloud? Existing IdP?
6. What's your ADA Title II remediation plan for AI-generated content?
7. Who owns the "no AI decides benefits/permits/records" policy line, and is it written down?

---

## 7. Anticipated questions & prepared answers (objection handling)
**"Isn't this just a chatbot?"** No. A chatbot answers. This *acts* across agencies — and the entire value is the governance around the action: authorization, consent, audit, rollback, and a human gate on every consequential decision.

**"How is this different from buying point solutions per agency?"** Point solutions give you N integrations, N security reviews, N audits, and no shared identity or audit trail. This is one governed substrate; every new agent inherits the controls, and a control improvement benefits all of them at once.

**"Will AI decide who gets benefits / a permit / a records release / a contract?"** No — by design and *in code*. Those commit actions are absent from every agent's grant set (`policy.py`) and the omission is enforced by an automated test. The deterministic eligibility engine runs outside the LLM; a human official owns the decision.

**"What about hallucinations in something a resident relies on?"** Every resident- or official-facing artifact passes deterministic grounding verification — any number, fee, date, or agency name not traceable to the source is flagged before a human sees it. Bedrock Guardrails add contextual grounding checks and PII filtering on top.

**"How do you handle CJIS, IRS 1075 FTI, HIPAA?"** Data classes are isolated by account/VPC boundary, not pooled; the masker strips SSNs, FTI, driver's licenses at every audit boundary; encryption is KMS CMK; access is least-privilege and fully logged. We ship a control-mappings matrix tying each regime to the concrete control.

**"GovCloud?"** Bedrock + Guardrails + Knowledge Bases are FedRAMP High / IL-4/5 in GovCloud. AgentCore is in GovCloud (US-West) but a few features aren't yet — so the platform uses the portable gateway path (API Gateway + STS) there, deploying day one. We pin that for you.

**"Is this lock-in?"** The gateway semantics are replicated in readable, testable Python (`platform_core/`), so the authorization model is portable. IaC ships as CloudFormation *and* Terraform. Agents are framework-light.

**"What happens if a step fails mid-transaction across agencies?"** The saga compensates — completed steps roll back in reverse order, and the evidence trail records both the commit and the undo. Demonstrated live: kill the 311 step and the prior step rolls back automatically.

**"How long to deploy?"** A scoped pilot (one agency, one workflow) is weeks, not quarters — it runs with no API key today; production-readiness (ATO, IdP integration, live connectors, pen test) is the engagement.

**"What's the accessibility story?"** AI-generated output is ADA Title II in-scope; we run deterministic WCAG checks (alt text, heading order, link purpose, plain-language grade) in CI and recommend axe-core for full auditing.

**"Who owns the data?"** The customer. Inference runs on Bedrock, reached from the VPC over AWS PrivateLink (a regional AWS service, not in-VPC hosting); constituent PII is masked at the audit and model-output boundaries (input filterable by Bedrock Guardrails, not blanket pre-scrubbed) with no egress to external AI APIs; the customer owns the KMS keys.

**"Why AWS?"** AgentCore (Runtime/Gateway/Identity), Bedrock + Guardrails, Step Functions for durable sagas, EventBridge for events, DynamoDB/S3 Object Lock for tamper-evident retention, GovCloud authorizations — the whole pattern is native and authorized.

---

## 8. Why it's scalable
**Technically:** serverless and event-driven (Step Functions, Lambda, EventBridge, DynamoDB on-demand) — it scales to zero and to spikes without re-architecture. The saga is generic: one state machine runs *any* life-event from its declarative step list.
**Organizationally:** adding an **agency** is a new canonical adapter + catalog entries; adding a **life-event** is a new template; adding an **agent** is a new specialist that plugs into the same gateway. Nothing in the core changes. That's how a customer goes from one life-event to many on one substrate.
**Governance scales with it:** a single improvement to the masker, grounding, or audit benefits all agents and all life-events simultaneously.

---

## 9. Estimated cost (TCO framework — validate against current AWS pricing)
> Figures are an **estimation framework**, not a quote. Plug in the customer's volume and current Bedrock pricing. The architecture is serverless, so cost tracks usage.

**Cost components**
| Layer | Driver | Notes |
|---|---|---|
| **Bedrock inference** | tokens per interaction × volume | Use Haiku for routing/classification, Sonnet for drafting; the largest variable cost |
| **Bedrock Guardrails** | per-policy text units evaluated | Applied on every model call |
| **Knowledge Bases / retrieval** | vector store (OpenSearch Serverless OCU or Aurora) + queries | A standing cost; shared across agents |
| **Step Functions** | state transitions per saga | Standard workflows; pennies per execution |
| **Lambda** | invocations + duration (ARM64) | Cheap; gate/step/compensate are short |
| **DynamoDB** | on-demand R/W + storage (audit, consent, events, idempotency) | PITR enabled |
| **S3 Object Lock (WORM)** | evidence storage + retention period | Retention-schedule driven |
| **EventBridge** | events published | Negligible at most volumes |
| **KMS, CloudTrail, CloudWatch** | keys, API events, logs/alarms | Baseline governance cost |

**Illustrative shape (customer plugs in real rates):**
- **Pilot (one agency, one workflow):** a small fixed platform baseline (retrieval + observability + tables) **plus** per-interaction inference. Typically modest 4-figure/month, dominated by retrieval standing cost and pilot volume.
- **Production (multi-agency):** the platform baseline is shared, so the marginal cost of each additional agent/life-event is mostly incremental inference — the **per-transaction cost falls as you add agents**, which is the core economic argument for the platform vs. point solutions.

**Cost levers to coach the architect on:** right-size the model tier per task (Haiku vs Sonnet), cache/scope retrieval, set Guardrail policies tightly, use DynamoDB on-demand + TTL on idempotency, and tune WORM retention to the actual records schedule.

**Funding path:** position AWS MAP / Proof of Concept funding and ISV/partner programs to underwrite the pilot — most SLG customers have no dedicated GenAI budget yet (NASCIO: only 25% do).

---

## 10. Regulatory alignment (summary — full matrix in `governance/controls/control_mappings.py`)
| Regime | How the platform aligns |
|---|---|
| **GovRAMP / FedRAMP** | Deploy on AWS authorized regions (GovCloud High / US Moderate) |
| **CJIS v6.0** | CJI account/VPC isolation; deny-by-default gateway; scoped tokens; masked audit |
| **IRS Pub 1075 (FTI)** | FTI data-class isolation; FTI masking; KMS; access logging; 6-yr WORM retention |
| **HIPAA / MARS-E→ARC-AMPE** | PHI masking; deterministic eligibility engine outside the LLM; least privilege |
| **FERPA** | Security-trimmed retrieval; consent; logging |
| **DPPA** | Driver's-license masking; purpose-bound tool scopes; recorded consent |
| **ADA Title II / WCAG 2.1 AA** | Accessibility checks on AI output in CI |
| **NIST AI RMF** | Grounding, prompt registry, evals, red team, fairness, HITL gates |

---

## 11. The land-and-expand motion
**Land:** one agency, one life-event or one agent, on the customer's AWS account, producing real audit evidence. **Prove:** ROI worksheet + the compliance evidence package + a CISO walkthrough. **Expand:** add agencies (adapters) and life-events (templates) on the same substrate; the platform baseline is already paid for, so each expansion is mostly incremental inference. **Anchor:** the whole-of-government orchestration layer becomes the customer's standard for all agentic government.

---

## 12. Proof points
Virginia Beach (1,300+ queries in month one) · Anne Arundel County (45 min → under 20s) · North Carolina "SCUBI" UI assistant (GovCloud, NIST AI RMF) · Kofile (3,000+ counties) · Grupo TX "TxGov" (~35% call-volume reduction). Sources in repo-root `SOURCES.md`.

## 13. Call to action
*"Let's pick one life-event and one agency, stand it up on your account in a scoped pilot, and put a real cross-agency audit trail in front of your CISO. Everything you saw today already runs — the pilot just points it at your systems."*
