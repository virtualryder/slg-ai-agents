# SLG Agentic AI — First-Meeting Cheat-Sheet (keep open during the call)
*One page. The full playbook is `gtm/SELLER-SA-FIELD-GUIDE.md`.*

**One-liner:** *"A governed, AWS-native accelerator — 8 SLG AI agents + an optional Whole-of-Government platform — where the agent isn't the product; the governance that makes it deployable, auditable, and compliant is."*

---
## The 8-step seller path
1. **Orient** — repo map in the Field Guide §0; decks live in `decks/`.
2. **Demo-ready** — run `demo/demo_run.py` (an agent) and `aws-native-reference/wog-platform/local_runner.py` (the saga + a rollback). No AWS, no API key.
3. **Qualify** — the 7 questions (right). Good sign: an engaged CISO + one owned workflow.
4. **Pick the deck** — deck picker (below).
5. **Run discovery** — frame → their pain → matching agent deck → live demo (pause at human gate → approve → audited) → next step.
6. **Security-fit (CISO)** — classify data → region/posture → map controls (`docs/COMPLIANCE-CONTROL-MAPPINGS.md`) → walk the architecture slide → set shared-responsibility → checklist.
7. **Architecture (SA)** — standalone first: `scripts/deploy.sh <agent> dev portable native`; add WoG later; follow `<agent>/docs/DEPLOY-RUNBOOK.md`.
8. **Commercialize** — scope a 1-agency/1-workflow pilot, position MAP/PoC funding, pick 1–2 grounded metrics, land-and-expand.

---
## The 7 qualifying questions
1. How many AI pilots run across your agencies — and who governs them?
2. When an agent touches a system of record, can you show an auditor *who authorized it* and *undo it*?
3. Which workflow hurts most — 311, forms, permitting, benefits, FOIA, procurement, IT tickets, or reports?
4. Commercial regions or **GovCloud**? Which **IdP** (Okta / Entra / Ping / Login.gov)?
5. Which **data classes** — CJI, FTI, PHI, education, PII?
6. What's your **ADA Title II** plan for AI-generated content?
7. Is there a written **"AI never decides X"** policy line? (If not — this gives them one.)

---
## Deck picker (`decks/`)
| If the room is… | Open |
|---|---|
| CIO/CISO, broad / strategic | `SLG-WoG-Orchestration-Platform.pptx` |
| "show me everything" overview | `SLG-Agentic-AI-Suite-Executive-Overview.pptx` |
| Benefits / HHS | `SLG-04-Benefits-Caseworker.pptx` |
| Public records / FOIA | `SLG-05-Public-Records-FOIA.pptx` |
| Permitting / licensing | `SLG-03-Permitting-Licensing.pptx` |
| Forms / document backlog | `SLG-02-Forms-IDP.pptx` |
| Resident services / 311 | `SLG-01-Resident-Services-311.pptx` |
| Procurement / grants | `SLG-06-Procurement-Grants.pptx` |
| IT service desk / modernization | `SLG-07-GovOps-Service-Desk.pptx` |
| Public safety / public health | `SLG-08-Public-Safety-Health.pptx` |
*(Talk track is in each deck's speaker notes; numbers cited in `decks/DECK-SOURCES.md`.)*

---
## The 5 CISO yes-makers (say these)
1. **Deny-by-default gateway** — the agent can never exceed the employee it acts for.
2. **Consequential actions withheld in code** — issue-permit / adjudicate / release / award aren't in the agent's grants (tested).
3. **Framework-enforced human gate** — no path to commit without approval.
4. **Tamper-evident audit + WORM** — append-only DynamoDB + S3 Object Lock; PII/CJI/FTI masked.
5. **Private-connectivity inference** — Bedrock via VPC endpoint (AWS PrivateLink) + mandatory Guardrails.

## Always say
*"You don't have to go all-in on whole-of-government. We start with one agent in its own secure VPC, prove it in front of your CISO, and grow agent by agent."*

## Proof points (cited in `SOURCES.md`)
Virginia Beach 1,300+ queries mo.1 · Anne Arundel 45 min → <20s · NC unemployment assistant · Kofile 3,000+ counties · Grupo TX −35% call volume.
