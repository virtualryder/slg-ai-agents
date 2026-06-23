# Whole-of-Government (WoG) Orchestration Platform
*The strategic layer: move from dozens of isolated chatbots to governed digital workers coordinated across agencies.*

Five pillars, each a module — all run with **no API key** (23 tests).

| Pillar | Module | What it provides |
|---|---|---|
| **Govern tool access** | `govern/tool_catalog.py` | The government tool gateway. Every cross-agency tool declares a contract — agency, allowed purposes (purpose binding), data classes, residency, read/write, transaction threshold, idempotency, rollback handler, approval — enforced *before* delegating to the deny-by-default MCP gateway. |
| **Canonical data layer** | `canonical/` | One `Resident`/`Address`/`CaseRef` contract; `AgencyAdapter`s map each agency's system-of-record shape ↔ canonical; `CanonicalRegistry` pins the schema version. |
| **Workflow coordination** | `saga/coordinator.py` | Durable cross-agency **saga with compensation**: forward + compensating action per step, consent + confirmation gates on material steps, idempotency (exactly-once), automatic rollback of completed steps on failure. |
| **Compliance events** | `events/` | Immutable, PII-masked event bus + a case-level **evidence assembler** with data-class→retention mapping and correlation IDs. |
| **Identity & consent** | `consent/` | AAL-gated (NIST 800-63), scoped, time-bound consent ledger; no cross-agency use without recorded consent. |

## How agents build on top
Specialist agents (01–08) register as handlers / saga step `forward` actions. They never hold cross-agency authority: each step still flows specialist → **GovernedToolGateway** → MCP gateway → connector, so `agent grant ∩ user entitlement`, purpose binding, scoped tokens, and audit all hold. The orchestrator and the saga coordinator hold **no tool grants**.

## Life-events shipped
`moving` · `job_loss` (PHI+FTI) · `new_business` · `disaster` (311 → assistance form → disaster benefits) · `bereavement` (estate form → death-record package → survivor benefits). Declarative templates in `saga/life_events.py` drive BOTH the in-process coordinator and the AWS-native Step Functions saga.

## See it run
```bash
PYTHONPATH=platform_core:. python gov_platform/wog_orchestration/demo/demo_life_event.py
```
A resident MOVES → three agencies (Shared Services, 311, City Clerk) commit as one saga; a second run injects a 311 outage and the completed step **rolls back**, with the evidence trail showing `compensated=True`. Architecture + AWS mapping: `docs/WOG-PLATFORM-ARCHITECTURE.md`.

## AWS-native, runnable
`aws-native-reference/wog-platform/` ships the saga as gate/step/compensate Lambdas + a generic Step Functions state machine, plus `local_runner.py` — a Step Functions emulator that executes the real Lambda handlers end-to-end with no AWS:
```bash
PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py
```
