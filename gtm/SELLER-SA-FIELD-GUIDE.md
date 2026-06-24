# SLG Agentic AI — Seller & SA Field Guide (START HERE)
*For an AWS seller + Solutions Architect taking this repository into a state/local government customer. Read this first. It tells you what this is, how to get smart on it fast, how to qualify and position it, which deck to use when, and how to make it fit the customer's security architecture.*

> **The one-liner:** *"A governed, AWS-native accelerator of 8 production-shaped SLG AI agents plus an optional Whole-of-Government orchestration platform — where the agent isn't the product; the governance that makes it deployable, auditable, and compliant is."*

---

## PHASE 0 — Orient (5 minutes): the repo map
| You need… | Go to |
|---|---|
| The pitch / talk track | `gtm/WOG-PLATFORM-GTM-STORY.md` |
| Customer-facing decks (one place) | `decks/` (8 agent decks + WoG + suite exec overview) — each has TIMING + talk-track in the **speaker notes** |
| Grounded numbers + citations on slides | `decks/DECK-SOURCES.md` |
| Reference architecture | `docs/SUITE-ARCHITECTURE.md`, `docs/WOG-PLATFORM-ARCHITECTURE.md` |
| Why the governance layer (CISO explainer) | `docs/WHY-THE-MCP-LAYER.md` |
| Standalone vs. platform deployment | `docs/DEPLOYMENT-MODELS.md` |
| Compliance control mappings | `docs/COMPLIANCE-CONTROL-MAPPINGS.md` + `governance/controls/control_mappings.py` |
| Sources for every claim | `SOURCES.md` |
| Per-agent deploy steps (real AWS) | `<agent>/docs/DEPLOY-RUNBOOK.md` |
| Platform deploy (16 stages) | `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` |
| Ops runbooks | `runbooks/` (incident, DR, model-degradation, HITL queue) |
| The code (proof it's real) | `platform_core/`, `gov_platform/`, the 8 agent folders, `infra/` |

**What it is, in one breath:** 8 governed agents (Resident Services/311, Forms/IDP, Permitting, Benefits, Public Records/FOIA, Procurement, GovOps service desk, Public Safety/Health), each deployable **standalone** with its own secure AWS stack, plus an **optional** Whole-of-Government platform that coordinates them across agencies for life events. 179 automated tests pass with no API key.

---

## PHASE 1 — Get smart fast (SA self-enablement, ~2 hours)
1. **Read in this order:** root `README.md` → `docs/DEPLOYMENT-MODELS.md` → `docs/SUITE-ARCHITECTURE.md` → `docs/WHY-THE-MCP-LAYER.md`.
2. **Run the demos (no AWS, no API key):**
   ```bash
   pip install -e platform_core
   PYTHONPATH=platform_core:. python -m pytest -q          # ~179 pass
   cd 01-resident-services-311 && EXTRACT_MODE=demo python demo/demo_run.py
   PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py   # 5 life-events + a rollback
   ```
3. **Internalize the 5 things that make a CISO say yes** (you will repeat these all day):
   - **Deny-by-default gateway, least-privilege intersection** — the agent can never exceed the human it acts for (`platform_core/.../mcp_gateway/policy.py`).
   - **Consequential actions withheld in code** — issue-permit / adjudicate / release-records / award are *absent from the agent's grants*, enforced by a passing test. A human owns them.
   - **Framework-enforced human gate** — `interrupt_before` / Step Functions `waitForTaskToken`; no path to commit without approval.
   - **Tamper-evident audit + WORM** — append-only DynamoDB + S3 Object Lock; PII/CJI/FTI masked at every boundary.
   - **In-account inference** — Bedrock via VPC endpoint + mandatory Guardrails; constituent data never leaves the VPC.
4. **Know the deployment switches:** Standalone vs WoG · commercial vs GovCloud · `portable` vs `agentcore` gateway · `native` vs `container` runtime.

---

## PHASE 2 — Qualify (is this a fit?)
**Ideal customer profile:** a state agency, county, or city with (a) AI on the roadmap (NASCIO #1 priority), (b) at least one high-volume, document/decision-heavy workflow, and (c) a security/compliance function that will ask hard questions (that's a *good* sign — this repo answers them).

**Qualifying questions (ask the CIO/CISO/program owner):**
1. How many AI pilots are running across your agencies, and who governs them?
2. When an agent touches a system of record, can you show an auditor *who authorized it* and *undo it*?
3. Which workflow hurts most — 311/resident services, forms backlog, permitting cycle time, benefits churn, FOIA backlog, procurement cycles, IT tickets, or report-writing?
4. Commercial regions or GovCloud? Existing IdP (Okta/Entra/Ping/Login.gov)?
5. What data classes are in play — CJI, FTI, PHI, education, PII?
6. What's your ADA Title II plan for AI-generated content?
7. Is there a written "AI never decides X" policy line? (If not, this gives them one.)

**Strong signals:** flat headcount + rising volume; an upcoming audit/ATO; a failed or ungoverned chatbot pilot; a GovRAMP/StateRAMP requirement.
**Disqualifiers / slow down:** wants fully autonomous decisioning (this intentionally won't), no security stakeholder engaged, or no single owned workflow to anchor a pilot.

---

## PHASE 3 — Position (frame per persona)
| Persona | What they care about | Lead with | Proof to show |
|---|---|---|---|
| **State CIO / CTO** | Pilots → production without 50 ungoverned bots | "One governed substrate; agents are configurations of it — controls compound, audits don't multiply." | WoG deck + 179 tests |
| **CISO** | Provable least privilege, audit, data isolation | "The agent can never exceed the employee, and the consequential action is withheld *in code*." | `policy.py` + withheld-action test + masked audit |
| **CFO / budget** | ROI, predictable cost, funding path | "Serverless pay-per-use; per-transaction cost falls as agents share the baseline; pilot fundable via AWS programs." | the agent deck's results slide + TCO framing in the GTM story |
| **Program director (HHS/Permitting/Records/Procurement)** | Throughput, backlog, constituent experience | the agent deck for *their* workflow + its grounded numbers | the per-agent deck + live demo |
| **Enterprise architect** | Reference architecture, IaC, no lock-in | "CloudFront→Cognito→VPC→Bedrock+Guardrails→WORM audit; CloudFormation + Terraform; commercial & GovCloud." | the architecture slide + `infra/` |
| **ADA / accessibility officer** | Title II for AI output | "AI output is accessibility-tested in CI." | `governance/accessibility/` |

**Always say:** "You don't have to go all-in on whole-of-government. We start with **one agent**, in its own secure VPC, prove it in front of your CISO, and grow agent by agent." (Standalone-first is the de-risking move — `docs/DEPLOYMENT-MODELS.md`.)

---

## PHASE 4 — Pick the deck (decision tree)
All decks are in `decks/` and carry a full speaker-note talk track.
- **First exec meeting / CIO+CISO, broad:** `SLG-WoG-Orchestration-Platform.pptx` (the strategic platform story) **or** `SLG-Agentic-AI-Suite-Executive-Overview.pptx` (one-deck tour of all 8).
- **A specific agency owns the pain:** the matching per-agent deck — e.g. Benefits → `SLG-04-Benefits-Caseworker.pptx`, FOIA → `SLG-05-Public-Records-FOIA.pptx`, Permitting → `SLG-03-Permitting-Licensing.pptx`. Each runs the same 6-slide arc: hook (grounded stats) → problem → governed solution pipeline → **AWS architecture & traffic flow** → tradeoffs/results.
- **Security deep-dive with the CISO:** drive from `docs/WHY-THE-MCP-LAYER.md` + the architecture slide + `docs/COMPLIANCE-CONTROL-MAPPINGS.md`.
- **Architecture review with the EA/SA:** the architecture slide + `docs/SUITE-ARCHITECTURE.md` + `infra/`.

> Tip: open decks in **Presenter View** — the per-slide TIMING + talk track is in the notes. Numbers are grounded; cite from `decks/DECK-SOURCES.md` if challenged.

---

## PHASE 5 — Run the discovery / first-call flow (45–60 min)
1. **(5m) Frame** — "AI is your #1 priority but most of it is ungoverned pilots. We brought a governed accelerator and a way to start small and secure."
2. **(10m) Their pain** — use the Phase-2 questions; let the program owner talk.
3. **(15m) Show the matching agent deck** — hook stats → the governed pipeline → the architecture slide. Pause on the human gate and the withheld action.
4. **(10m) Live demo** — run the agent's `demo/demo_run.py` (no AWS); show intent→action→**paused at human gate**→approve→committed + audited. For the platform, run `local_runner.py` and show the **rollback** on a forced failure.
5. **(10m) Security + deployment model** — standalone-first; their data classes; commercial vs GovCloud. Hand the CISO `WHY-THE-MCP-LAYER.md`.
6. **(5m) Next step** — propose a scoped pilot (one agency, one workflow) and name the success metric.

---

## PHASE 6 — Make it fit the customer's security architecture (the CISO workstream)
This is where deals are won or lost in SLG. Walk it explicitly.

**6.1 Classify the data.** Identify every data class the workflow touches — **CJI, FTI, PHI, education (FERPA), DMV (DPPA), PII, PCI**. This drives isolation, region, retention, and notification duties.

**6.2 Pick the boundary & region.**
- **Commercial regions, GovCloud-ready** is the default and deploys day-one. **GovCloud (US)** when FedRAMP High / IL-4/5 or contract terms require it — note Bedrock + Guardrails + Knowledge Bases are FedRAMP High/IL-4/5 in GovCloud, and AgentCore is GovCloud-limited, so **use the `portable` gateway path in GovCloud**.
- **Data-class isolation:** separate accounts/VPCs per class (CJI/FTI/PHI/EDU/public) — not one pooled boundary. (AWS Organizations / Control Tower.)

**6.3 Map controls to their regimes.** Hand the CISO `docs/COMPLIANCE-CONTROL-MAPPINGS.md`. The platform control → regime mapping (deny-by-default gateway, masking, WORM audit, KMS, Guardrails, accessibility, NIST AI RMF) covers **GovRAMP/StateRAMP, CJIS v6.0, IRS Pub 1075, HIPAA/MARS-E→ARC-AMPE, FERPA, DPPA, ADA Title II, PCI**. Be clear what's **Implemented** vs **Configurable** (customer must wire IdP, validate connectors, set Guardrail policy, set retention to their schedule).

**6.4 Walk the security architecture (the diagram slide).** Edge: **CloudFront + AWS WAF (managed rules/OWASP, rate-limit) + Shield**. Identity: **Cognito federates their IdP → short-lived JWT**; API Gateway JWT authorizer validates it; the **MCP gateway re-checks the `custom:slg_role` claim** and mints a **scoped per-call token** (no standing service accounts). Model: **Bedrock via VPC endpoint + mandatory Guardrails**. Data: **append-only audit + S3 Object Lock (WORM)**, **KMS CMK per data class**. Ops: CloudTrail, GuardDuty, Security Hub, Config.

**6.5 Set the shared-responsibility line.** The accelerator provides the *control design*; the customer operationalizes: ATO/GovRAMP, IdP integration + role mapping, connector validation against live systems, Guardrail tuning, retention schedule, and a CSV/validation for the intended use. Say this out loud — it builds trust.

**6.6 Run it through Well-Architected + the GenAI Lens** during the SA's review; the controls above map cleanly to Security, Reliability, and Operational Excellence.

**6.7 Hand the review board the gap assessment + RACI.** `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` states what's built vs. to-build (live connectors, ATO/GovRAMP, pen test) and who owns each piece (AWS · Partner · Customer) — it pre-answers the board's hardest questions and frames the engagement scope honestly.

**6.8 Security review checklist (give to the CISO):**
- [ ] Data classes identified; isolation boundaries chosen
- [ ] Region/posture (commercial | GovCloud) + gateway path decided
- [ ] IdP federation + `custom:slg_role` mapping designed
- [ ] Guardrail mandatory in prod (`ENVIRONMENT=production` fails closed without one)
- [ ] Audit append-only (SCP deny Update/Delete) + WORM retention = their records schedule
- [ ] Connectors validated against live systems
- [ ] HITL queue + approver-identity enforcement tested
- [ ] Accessibility (axe-core + manual) for AI output
- [ ] Incident / DR / model-degradation runbooks reviewed

---

## PHASE 7 — Architecture & deployment fit (the SA workstream)
- **Standalone first** (recommended): `scripts/deploy.sh <agent> <env> portable native` deploys a complete isolated stack — **own VPC + Flow Logs + Bedrock endpoint** (`network.yaml`), **CloudFront + WAF + Shield** (`edge.yaml`), KMS/Guardrail/Cognito (`security.yaml`), WORM audit (`data.yaml`), gateway, agent. No WoG dependency.
- **Add WoG later** (`infra/cloudformation/wog-platform.yaml`) when they want cross-agency life-event orchestration; the same agents become saga steps with no rewrite.
- **IaC parity:** CloudFormation primary + Terraform (`infra/terraform/`, incl. a GovCloud overlay).
- **Follow the runbooks:** per-agent `docs/DEPLOY-RUNBOOK.md` (numbered, with Verify checkpoints) and the 16-stage `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`.

---

## PHASE 8 — Commercialize (close + expand)
1. **Scope a pilot:** one agency, one workflow, their IdP + one knowledge source, their AWS account — producing real audit evidence. Weeks, not quarters (it runs locally today).
2. **Funding:** position AWS **MAP / Proof-of-Concept** funding (most SLG customers have no dedicated GenAI budget yet — NASCIO: only 25% do).
3. **Success metrics:** pick 1–2 grounded to the agent (deflection %, cycle-time, backlog, MTTR, report-time) from the deck's results slide; baseline before, measure after.
4. **Land-and-expand:** the platform baseline is shared, so each added agent/life-event is mostly incremental inference — **per-transaction cost falls as you scale.** Grow agent by agent into the WoG platform.

---

## PHASE 9 — Objection handling & proof points
Full Q&A is in `gtm/WOG-PLATFORM-GTM-STORY.md` (§7). The greatest hits:
- *"Isn't this just a chatbot?"* → It *acts* across systems; the value is the governance around the action.
- *"Will AI decide benefits/permits/records/awards?"* → No — withheld in code, enforced by a test; deterministic engines + humans decide.
- *"Hallucinations?"* → Deterministic grounding + Guardrail contextual-grounding checks before a human sees output.
- *"GovCloud / CJIS / FTI?"* → Mapped; portable gateway path in GovCloud; data-class isolation; masking.
- *"Lock-in?"* → Gateway logic is readable/testable Python; CloudFormation **and** Terraform.
**Proof points (cited in `SOURCES.md`):** Virginia Beach (1,300+ queries mo.1), Anne Arundel (45 min→<20s), NC unemployment assistant, Kofile (3,000+ counties), Grupo TX (35% call-volume cut).

---

## TL;DR — the seller's 8-step path
1. Skim Phase 0 map → 2. Run the demo (Phase 1) → 3. Qualify with the 7 questions (Phase 2) → 4. Pick the deck (Phase 4) → 5. Run the discovery flow + live demo (Phase 5) → 6. Drive the CISO security-fit workstream + checklist (Phase 6) → 7. SA scopes the standalone deployment (Phase 7) → 8. Scope a funded pilot and a metric (Phase 8).
