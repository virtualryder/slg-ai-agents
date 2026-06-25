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
| Decks (`decks/`) | 8 per-agent + WoG + suite exec overview — **rebuilt on the AWS template** (squid-ink/orange/teal), 6-slide narrative, **true AWS architecture diagrams** (boxes + Cognito-JWT traffic flow + control cards), **grounded results from named deployments** (State of California permitting, Anne Arundel, Denver "Sunny", DOJ FOIA, Nevada DETR, CDC TowerScout, IBM/ServiceNow), **evidence-tier labeled on-slide** ([GOV]/[PEER-REVIEWED]/[VENDOR-REPORTED]/[ANALYST]); counter-evidence + caveats in **speaker notes**; Honolulu removed (`decks/DECK-SOURCES.md`) | 10 ✓ |
| Seller / SA enablement | `gtm/SELLER-SA-FIELD-GUIDE.md` (9-phase playbook) + `gtm/SELLER-FIRST-MEETING-CHEATSHEET.md` (one-pager) | — |
| Per-agent deploy runbooks | `<agent>/docs/DEPLOY-RUNBOOK.md` (real-AWS, step-by-step) for all 8 | — |
| Production-readiness & RACI | `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md` — gap assessment + shared-responsibility matrix + go-live checklist | — |
| Sources | `SOURCES.md` verified Jun 2026 | — |

**Totals: 179 automated tests passing with no API key + 2 eval cases.** See `IMPROVEMENTS-OVER-EDU-HCLS.md` for the backlog.
