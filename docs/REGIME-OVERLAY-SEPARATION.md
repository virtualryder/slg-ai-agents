# Regime-overlay separation — SLG AI Agent Suite

**The point.** Not every SLG agent handles criminal-justice data, federal tax information, or
protected health information — so not every agent should inherit the highest control path. This doc
separates the suite into **data-class-driven regime overlays** so a deployment applies CJIS controls
only where criminal-justice information (CJI) actually flows, IRS Pub 1075 controls only where federal
tax information (FTI) flows, and so on. This complements
[`COMPLIANCE-CONTROL-MAPPINGS.md`](COMPLIANCE-CONTROL-MAPPINGS.md) and the
[`NIST-800-53-CONTROL-MATRIX.md`](NIST-800-53-CONTROL-MATRIX.md). It is **not legal advice and not an
authorization** — the deploying agency's ISO/privacy officer owns the determination.

## Baseline vs overlays

Every agent runs on the **SLG governance baseline** (the AGP controls: deny-by-default gateway,
least-privilege intersection, bound single-use SoD approvals, fail-closed masking, append-only + WORM
audit, token budgets, model gateway + guardrails, NIST 800-53 / NIST AI RMF mappings). Overlays add
regime-specific controls **only** for agents whose data class requires them.

| Overlay | Trigger data class | Adds on top of baseline |
|---|---|---|
| **CJIS v6.0** | Criminal justice information (CJI) | CJIS-compliant identity assurance & MFA, advanced auth, CJI-specific audit content, personnel screening attestations, incident reporting to the CSA, CJI entity masking in guardrails |
| **IRS Pub 1075** | Federal tax information (FTI) | FTI-specific access controls & need-to-know, 1075 audit-trail content, disclosure accounting, safeguard reporting (SAR/plan), FTI masking |
| **HIPAA / CMS MARS-E** | Protected health information / exchange data (benefits eligibility) | BAA path, PHI masking, MARS-E → ACA-AMPE control set, minimum-necessary enforcement |
| **FERPA / state student-privacy** | Education records (where an SLG workflow touches them) | Directory-vs-education-record distinction, disclosure logging, parent/eligible-student rights handling |
| **Public-records / FOIA** | Records subject to disclosure | Redaction-before-release controls, exemption handling, disclosure audit |

## Per-agent overlay assignment (default; deployment may adjust)

| # | Agent | Primary data class | Overlays that apply | Overlays that do **not** |
|---|---|---|---|---|
| 01 | Resident Services (311) | Public / low-sensitivity PII | Baseline (+ FOIA if it surfaces records) | CJIS, 1075, HIPAA |
| 02 | Forms / IDP | Mixed PII (form-dependent) | Baseline; overlay by form data class | Assign narrowly — don't blanket CJIS |
| 03 | Permitting & Licensing | Business/PII | Baseline (+ FOIA) | CJIS, 1075, HIPAA |
| 04 | Benefits Caseworker | **FTI + PHI** (eligibility) | **IRS 1075 + HIPAA/MARS-E** | CJIS |
| 05 | Public Records / FOIA | Records for disclosure | **FOIA/redaction** overlay | CJIS, 1075 (unless a record contains them) |
| 06 | Procurement & Grants | Business/financial PII | Baseline (+ FOIA) | CJIS, 1075, HIPAA |
| 07 | GovOps Service Desk | Internal ops / low PII | Baseline | CJIS, 1075, HIPAA |
| 08 | Public Safety & Health | **CJI** (+ PHI for the health portion) | **CJIS v6.0** (+ HIPAA where health data flows) | 1075 |

This assignment is why the golden-path templates tune guardrail entity sets and audit content
**per agent** (CJI for 08, FTI/PHI for 04) rather than forcing one maximal profile onto all eight —
verified in `infra/golden-path-04-benefits-caseworker/template.yaml` and
`infra/golden-path-08-public-safety-health/template.yaml`.

## Why separation matters (and the risk of not doing it)

- **Over-scoping is a real cost.** Applying CJIS personnel-screening and identity-assurance to a 311
  FAQ agent that never touches CJI adds cost and delay with no risk reduction, and can *stall* a
  low-risk, high-value pilot.
- **Under-scoping is a compliance failure.** Missing the 1075 overlay on the benefits agent (which
  does touch FTI) is a safeguard gap.
- **The data class, not the agent name, drives the overlay.** If a deployment routes a new data class
  through an agent, re-evaluate its overlay — the agent manifest declares its data classes, and the
  gateway enforces that an agent cannot exceed them.

## How this is enforced, not just documented

- The **agent manifest** declares each agent's permitted data classes; the deny-by-default gateway
  rejects any tool call outside them (an FTI tool is unreachable from a baseline-only agent).
- **Guardrail entity sets and masking** are configured per data class in the golden-path templates.
- **Audit content** carries the regime-required fields for the overlays in force.

## Customer-owned

The agency's authorizing official determines applicability, executes the CJIS/1075/BAA agreements and
attestations, completes personnel screening, and files the required safeguard/incident reports. This
repo provides the control scaffolding and the data-class-driven separation — not the authorization.
See [`../assurance/README.md`](../assurance/README.md) and
[`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md).
