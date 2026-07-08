# Worked ROI case study — Resident Services / 311 (Agent 01)

**What this is.** A fully worked, illustrative ROI example with totals — the value counterpart to
[`TCO-MODEL.md`](TCO-MODEL.md). Illustrative, source-tagged assumptions; not a guarantee or a customer
result. Replace bracketed inputs with the agency's actuals. `[MODEL ASSUMPTION]` marks editable
drivers.

## Scenario: a mid-size city, 311 / resident services

| Input | Value | Source |
|---|---|---|
| Annual 311 contacts | 1,000,000 | `[MODEL ASSUMPTION]` |
| Share that are routine/deflectable (status, hours, how-to, forms) | 60% → 600,000 | `[GOV]` typical deflectable share |
| Fully-loaded cost per human-handled contact | $8.01 | `[ANALYST]` Gartner service-contact economics |
| Cost per AI-handled contact | ~$0.10 | `[MODEL ASSUMPTION]` |
| Target automation rate on deflectable volume | 50% (phased) | `[MODEL ASSUMPTION]` conservative |

## The intervention

Agent 01 answers routine resident questions and drafts service-request tickets through the governed
gateway — **ticket submission and any consequential action are human-gated**. Value lever: deflect
routine contacts from live agents at ~$0.10 vs ~$8.01.

## Worked value (illustrative)

| Line | Calculation | Annual value |
|---|---|---|
| Contacts automated | 600,000 × 50% | 300,000 |
| Cost today (human) | 300,000 × $8.01 | $2,403,000 |
| Cost with AI | 300,000 × $0.10 | $30,000 |
| **Gross annual saving (illustrative)** | $2.403M − $30K | **~$2.37M** |

## Cost side (from TCO-MODEL.md)

| Line | Annual |
|---|---|
| AWS run cost (production scale, from TCO-MODEL) | ~$38,760/yr |
| Implementation + integration (one-time, engagement) | `[MODEL ASSUMPTION]` $150,000–$350,000 |

## ROI

Gross saving ~$2.37M vs ~$39K/yr AWS + a one-time build → payback in **well under a quarter** even at a
conservative 50% automation of deflectable volume. For the CIO/CFO: **311 is the lowest-blast-radius,
highest-volume place to prove the governed pattern** — measurable, low-risk, and the AWS cost is
immaterial to the saving.

## Honesty rails

- Illustrative model, not an agency outcome or guarantee. Deflectable share and per-contact cost vary
  — use actuals; start with a synthetic pilot.
- The agent answers and drafts; **humans own consequential actions**. Value assumes that model.
- Bedrock token volume is the dominant variable cost (see TCO-MODEL sensitivity); immaterial to this
  ROI at any realistic volume.
- Phase the automation rate up as confidence grows — don't quote 100% on day one.
