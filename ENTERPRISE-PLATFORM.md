# The SLG Enterprise Platform Story

**The pitch is the platform, not the chatbots.** A state or municipality that buys eight point chatbots gets eight ungoverned integrations and eight audits. A state that buys this platform gets one governed substrate — identity, authorization, audit, retention, accessibility, model-risk control — and the agents become *configurations* of it.

## Five reusable accelerators (map to the 8 agents)
1. **Resident Services Agent** — public knowledge, 311, status, appointments, multilingual, contact-center handoff.
2. **Government Forms & Case Agent** — completion, extraction, intake, routing, correspondence (foundation for permits, licenses, benefits, incident reports, grants).
3. **Caseworker & Reviewer Agent** — policy retrieval, evidence assembly, missing-info detection, draft notices, human review (HHS, UI, child welfare, revenue, public safety packs).
4. **Public Records & Transparency Agent** — digitization, metadata, search, FOIA discovery, redaction, translation, accessible publication.
5. **GovOps Agent** — IT service desk, procurement, grants, HR, contract admin, modernization, security ops.

## What every accelerator ships with (and this repo demonstrates on Agent 01)
Reference architecture · infrastructure as code · evaluation datasets · guardrails · API/MCP tool templates · human-approval patterns · records-retention configuration · accessibility testing · compliance-control mappings · KPI dashboard.

## ADR-001 — Orchestration
In-process LangGraph specialists today; the **WoG orchestrator** (`gov_platform/wog_orchestration/`) coordinates cross-agency life-events with consent + confirmation gates. Move specialists to AgentCore Runtime + A2A when they deploy as independent services; the gateway path and gates are unchanged.

## The long game
Common agent identity, governed tool access, canonical data, workflow coordination, and shared compliance evidence is what lets a government move from dozens of isolated chatbots to controlled digital workers that actually improve service delivery.

---

## Why dive deeper — the whole-of-government prize (grounded)
*Every claim below is factual and cited; no aspirational hand-waving.*

**The reframe that changes everything.** Today a resident who **moves** files a change of address with the DMV, separately updates voter registration, separately starts trash service, separately re-enrolls a child in school — four agencies, four systems, four logins, and no one with the whole picture. The same fragmentation repeats for the handful of moments that matter most in a person's life: **a new child, starting a business, losing a job, a disaster, a death in the family.** This platform organizes government around those **life events**, not the org chart. Those five life events are **implemented and runnable today** (`gov_platform/wog_orchestration/`), each as a durable, compensating cross-agency transaction.

**Why the timing is real, not hype.**
- AI is the **#1 state-CIO priority for 2026** (NASCIO), displacing cybersecurity for the first time in over a decade.
- Yet **90% of states are still in pilots and only 25% have dedicated GenAI funding** (NASCIO) — the field is wide open, and the differentiator is governance, not models.
- The tooling is authorized: **Amazon Bedrock AgentCore is GA** (Oct 2025) and reached **GovCloud** (May 2026); **Bedrock + Guardrails + Knowledge Bases are FedRAMP High / DoD IL-4/5** in GovCloud.
- The clock is ticking: **ADA Title II** accessibility deadlines hit **Apr 2027 / Apr 2028**, and AI-generated output is explicitly in scope.

**Why it works where others stall — the engineering, not the marketing.** The obstacle to whole-of-government service was never the model; it is identity, consent, interagency authority, and one audit trail. The platform solves exactly those:
- There is **no two-phase commit** across a DMV, an HHS eligibility system, and a 311 CRM — so it uses a **durable saga with compensation**: if a downstream agency fails mid-transaction, completed steps **roll back in reverse order** and the evidence records the undo. *Nobody is ever left half-enrolled.* This is **demonstrated and tested** — run `aws-native-reference/wog-platform/local_runner.py` and watch a forced 311 outage roll back the prior step.
- **Authority never concentrates:** the orchestrator holds **no tool grants**; every write still flows through a specialist agent's deny-by-default gateway, and a human owns every consequential decision.
- **One auditable record:** every step and every rollback emits an immutable, retention-aware compliance event partitioned by case — the unified trail an auditor, a FOIA request, or an appeal needs.

**Why the economics improve as you scale (factual, not projected).** The platform is serverless and the governance baseline (identity, gateway, audit, retention, accessibility) is **shared**. So the marginal cost of each additional agent or life-event is mostly incremental Bedrock inference — the **per-transaction cost falls as you add agents.** That inverts the point-solution model, where every new chatbot adds another integration, another security review, and another audit.

**Proof it's grounded in real deployments** (all AWS public-sector, cited in `SOURCES.md`): Virginia Beach (1,300+ queries in month one), Anne Arundel County (45 min → under 20 seconds), North Carolina (a GenAI unemployment assistant on GovCloud), Kofile (3,000+ counties), Grupo TX (−35% call-center volume, 50% faster responses).

**The honest framing.** This is a production-shaped **accelerator**, not a finished SaaS: the integrations run against realistic fixtures (each deployment needs live connectors and a hardening sprint), and the figures are documented results from named deployments and published benchmarks applied to a reference agency — not a longitudinal study. What's real today: **5 life-events, a runnable compensating saga, deployable IaC for commercial and GovCloud, and 179 automated governance tests that pass with no API key.**

**The one sentence to take upstairs.** *A state doesn't need fifty chatbots; it needs one governed substrate that lets digital workers act across agencies and be defended in front of an auditor — and that substrate is what turns dozens of isolated demos into digital government.*

> Dive deeper: `docs/WOG-PLATFORM-ARCHITECTURE.md` (the five pillars → AWS services), `gtm/WOG-PLATFORM-GTM-STORY.md` (the pitch + objection handling), and `decks/SLG-WoG-Orchestration-Platform.pptx` (the executive deck, with a full talk track in the notes).
