# Suite Status

| Component | State | Tests |
|---|---|---|
| `platform_core` (gateway, masker, LLM factory, connectors, A2A) | Flagship | 29 ✓ |
| `governance` (grounding, prompts, evals, red team, fairness, accessibility, controls) | Flagship | 16 ✓ + 2 evals |
| `gov_platform/wog_orchestration` (govern-tool-access · canonical+adapters · consent · events+evidence · **saga w/ compensation** · **5 life-event templates**) | Flagship | 30 ✓ |
| WoG saga AWS-native (gate/step/compensate Lambdas, **DynamoDB+EventBridge backends**, Step Functions emulator) | Deployable + live-ready | 14 ✓ |
| Agent 01 — Resident Services & 311 | Flagship (LangGraph + tools + 4 docs + app + container) | 7 ✓ / 1 skip |
| Agent 01 AWS-native (Strands + Step Functions) | Deployable reference | 5 ✓ |
| Agents 02–08 (forms-idp · permitting · benefits · records-foia · procurement · govops · public-safety) | Flagship — **per-intent action mapping**, withheld consequential actions, 4 docs + **deploy runbook** + **customer deck** each, AWS-native rebuilds | 63 ✓ |
| IaC — CloudFormation (6 templates) | Valid, deployable | parsed ✓ |
| IaC — Terraform + GovCloud overlay (6 files) | Valid HCL | parsed ✓ |
| Decks (`decks/`) | 8 per-agent + WoG + suite exec overview — example-style 6-slide narrative, **true AWS architecture diagrams** (boxes + traffic flow), **grounded results from named deployments** (Nevada DETR, Honolulu, CDC, Leon County, IBM/ServiceNow), vendor/peer-reviewed labeled, RCT counter-evidence on-slide; talk tracks in notes (`decks/DECK-SOURCES.md`) | — |
| Seller / SA enablement | `gtm/SELLER-SA-FIELD-GUIDE.md` (9-phase playbook) + `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md` (one-pager) | — |
| Per-agent deploy runbooks | `<agent>/docs/DEPLOY-RUNBOOK.md` (real-AWS, step-by-step) for all 8 | — |
| Sources | `SOURCES.md` verified Jun 2026 | — |

**Totals: 179 automated tests passing with no API key + 2 eval cases.** See `IMPROVEMENTS-OVER-EDU-HCLS.md` for the backlog.
