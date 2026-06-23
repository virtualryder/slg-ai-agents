# Suite Status

| Component | State | Tests |
|---|---|---|
| `platform_core` (gateway, masker, LLM factory, connectors, A2A) | Flagship | 29 ✓ |
| `governance` (grounding, prompts, evals, red team, fairness, accessibility, controls) | Flagship | 16 ✓ + 2 evals |
| `gov_platform/wog_orchestration` (govern-tool-access · canonical+adapters · consent · events+evidence · **saga w/ compensation** · **5 life-event templates**) | Flagship | 30 ✓ |
| WoG saga AWS-native (gate/step/compensate Lambdas, **DynamoDB+EventBridge backends**, Step Functions emulator) | Deployable + live-ready | 14 ✓ |
| Agent 01 — Resident Services & 311 | Flagship (LangGraph + tools + 4 docs + app + container) | 7 ✓ / 1 skip |
| Agent 01 AWS-native (Strands + Step Functions) | Deployable reference | 5 ✓ |
| Agents 02–08 | Scaffolded (folders + slots) | — |
| IaC — CloudFormation (6 templates) | Valid, deployable | parsed ✓ |
| IaC — Terraform + GovCloud overlay (6 files) | Valid HCL | parsed ✓ |
| Decks | Agent 01 + suite exec overview + **WoG platform** | — |
| Sources | `SOURCES.md` verified Jun 2026 | — |

**Totals: 102 automated tests passing with no API key + 2 eval cases.** See `IMPROVEMENTS-OVER-EDU-HCLS.md` for the backlog.
