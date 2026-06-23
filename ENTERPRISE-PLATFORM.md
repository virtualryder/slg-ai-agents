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
