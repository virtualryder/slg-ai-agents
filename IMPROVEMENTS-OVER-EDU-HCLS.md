# What's Better Here Than EDU/HCLS — and What to Improve Next

You asked me to build to the EDU/HCLS bar as a minimum and exceed it. Here is exactly how this SLG suite raises the bar, plus the honest backlog.

## Where SLG exceeds the prior suites
1. **Consequential actions are withheld in code, not just documented.** EDU/HCLS lean on the HITL gate for write safety. Here the *legally consequential commit* (issue permit, adjudicate eligibility, release records, award contract) is **absent from every agent's grant set** in `policy.py` and the omission is enforced by a passing test (`test_consequential_actions_withheld_from_agents`). Defense-in-depth: even a mis-scoped human role can't let the agent commit.
2. **Accessibility is a first-class governance control.** EDU/HCLS have no accessibility gate. SLG adds `governance/accessibility/wcag.py` (alt text, heading order, link purpose, Flesch-Kincaid plain-language) wired into the agent's `compliance_check` and CI — because ADA Title II puts AI-generated output in scope (deadlines now 2027/2028).
3. **A real Whole-of-Government Orchestration Platform**, not just an A2A note. `gov_platform/wog_orchestration/` ships canonical data, an AAL-gated consent ledger, a compliance event bus, and a life-event orchestrator that **requires explicit resident confirmation before each material action** — with tests.
4. **Masker widened to government data classes.** Beyond PHI: driver's license (DPPA), FTI/EIN (IRS 1075), case/permit/FOIA IDs, and street addresses.
5. **Disparate-impact testing built in** (`governance/fairness/`, four-fifths rule) for any flag/rank workflow — the civil-rights exposure unique to government.
6. **Full IaC parity from day one for commercial *and* GovCloud**, with the GovCloud AgentCore carve-outs (Memory/semantic-search/Policy/Registry not yet available) handled by pinning the portable gateway path — a currency detail most references miss.
7. **Currency corrections captured in `SOURCES.md`:** ADA 2027/2028 deadlines, MARS-E→ARC-AMPE, AgentCore GA + GovCloud status, Strands 1.0, named 2026 deployments.

## Honest backlog (next passes)
- **Agents 02–08** are scaffolded; replicate Agent 01's flagship depth (graph + tools + docs + native rebuild + deck) across them. Agent 01 is the gold template.
- **Per-agent decks** for 02–08 and the suite executive overview (Agent 01 deck + suite deck shipped this pass).
- **Live connectors** for Accela/Tyler, the integrated eligibility system, ECMS/records, ServiceNow — interfaces are defined; adapters are stubs.
- **Bedrock Knowledge Base ingestion** pipeline (the retrieval substrate is referenced; the ingestion IaC is a stub).
- **axe-core CI job** to complement the deterministic WCAG pre-flight with full automated auditing.
- **Cedar/OPA policy export** — generate AgentCore Gateway targets + Cedar policies directly from `policy.py` so the Python model and the deployed authorizer can't drift.
- **Offerings depth** (battlecard, SOW, TCO) — port and SLG-tailor from HCLS.
