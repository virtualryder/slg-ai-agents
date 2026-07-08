# Decks

Customer-facing presentation decks. **Single source of truth — do not duplicate elsewhere.**

All 10 decks are rebuilt on the **AWS interview-deck template** (squid-ink navy `#232F3E` + AWS orange `#FF9900` + teal `#01A88D` human-gate), matching `AWS-Interview-Presentation-v2.pptx`. Each follows one **6-slide narrative**, and every slide carries a **timed talk-track in the speaker notes** (open in PowerPoint → View → Notes Page, or use Presenter View).

| File | Use |
|---|---|
| `SLG-01-Resident-Services-311.pptx` … `SLG-08-Public-Safety-Health.pptx` | Per-agent customer/executive decks (8) |
| `SLG-WoG-Orchestration-Platform.pptx` | Whole-of-Government platform — the CIO/architect strategic deck |
| `SLG-Agentic-AI-Suite-Executive-Overview.pptx` | One-deck overview of all 8 agents + the platform (the opener / leave-behind) |
| `SLG-Agentic-AI-Suite-COMBINED.pptx` | **All 10 decks merged into one 60-slide walkthrough** (suite overview → agents 01–08 → WoG), full speaker notes preserved — for a single end-to-end session |

## The 6-slide narrative (every deck)

1. **Title** — agent name, "governed agentic AI on AWS," presenter block.
2. **Hook — FROM X TO Y** — one hero transformation + three grounded stat callouts. The slide you lead with.
3. **Customer & the problem today** — who they are, what they live with, and the **cost of the status quo** as hard numbers.
4. **The agent workflow** — a numbered, governed pipeline with the **teal human gate**: the consequential action is *withheld in code* until a person approves.
5. **AWS reference architecture** — a true box-diagram with numbered traffic flow (**Cognito JWT exchange shown**), four regulated-environment control cards (identity/least-privilege, data protection, AI guardrails/HITL, compliance posture), and the standalone-vs-WoG deployment band.
6. **What good looks like (results / ROI)** — documented outcomes from **named deployments**, each tagged by evidence tier, plus the one-line executive case.

## How to present — by audience

These decks are built to resonate with three buyers. The talk-track in each slide's notes calls out where to lean in:

- **CIO / Director** — lead with slide 2 (the hook) and slide 6 (ROI / executive case). The story is escaping the "pilot trap": build governance once, every future agent inherits it.
- **CISO** — slow down on slide 5. Walk the Cognito→JWT→API Gateway→MCP-gateway exchange, the deny-by-default least-privilege model (effective scope = *agent grant ∩ user entitlement*), PII masking, **S3 Object Lock (WORM)** audit, and **Bedrock FedRAMP High + DoD IL-4/5 in GovCloud**. (Say it precisely: those **Bedrock services** carry that authorization in GovCloud; the **accelerator is not itself FedRAMP-authorized**.) The "consequential action withheld in code" line on slide 4 is the trust anchor.
- **Director of Architecture** — slides 4 and 5 are the substance: the governed pipeline and the reference architecture map directly to the IaC (CloudFormation + Terraform, commercial + GovCloud) and container code in each agent folder.

**Sequencing tip (in the suite-overview notes):** lead with the agent that fits the room — **311** for citizen value, **benefits** for mission, **public safety** for credibility — then sell the **platform** underneath.

## One-page leave-behinds (`leave-behinds/`)

All **10** items (8 agents + the WoG platform + the suite overview) have a **single-page seller leave-behind** (portrait letter, same AWS theme) in `decks/leave-behinds/` — as both **PDF** (email/print) and editable **PPTX**. Layout: header → **FROM-X-TO-Y** hook → **The Problem** → **The Governed Solution** (numbered pipeline + teal human gate) → **The ROI** (named-deployment stats + executive case) → **Security & Compliance** (the four control areas) → deploy/footer.

`SLG-AI-Agents-ALL-OnePagers.pdf` is the **combined distribution PDF** — all 10 pages in one file, ordered suite overview → agents 01–08 → WoG platform. Send the whole portfolio, or pull a single page.

Use the **deck to sell in the room, the one-pager to survive the forward** — it's what a champion emails to the CIO/CISO/architect after the meeting. Figures and labels match the decks and `DECK-SOURCES.md`.

## Sourcing discipline (read before presenting)

- Every figure is grounded and labeled by evidence tier in **`DECK-SOURCES.md`** — **[GOV]**, **[PEER-REVIEWED]**, **[VENDOR-REPORTED]**, **[ANALYST]**. On-slide tags show the tier; speaker notes give the precise attribution.
- **Lead public-safety with CDC TowerScout** — the only government *and* peer-reviewed anchor in the library.
- **Counter-evidence and caveats live in the speaker notes, not on the slides** (a deliberate design choice). Example: the public-safety deck's notes carry the pre-registered **null-result RCT** and the Anchorage PD non-renewal on AI police-report writing. **Volunteer these when asked** — the candor is what earns a CISO's trust.
- The prior **Honolulu / CivCheck** permitting figure has been **removed** (unvalidated) and replaced with the **State of California (Newsom, Apr 2025)** AI plan-review announcement — a [GOV] source in which Amazon is a named contributing partner.

Numbers are documented outcomes from named deployments and published benchmarks applied to a reference agency — not a longitudinal guarantee; the notes say so.

## Regenerating the decks

The decks are generated from a small Node engine (kept in the working scratchpad, not committed): `engine.js` (template renderer + palette), `specs.js` (per-deck content + speaker notes), `build.js` (runner). To rebuild: `npm install pptxgenjs && node build.js ./out`, then copy the `.pptx` files here. Update `DECK-SOURCES.md` whenever a figure changes.
