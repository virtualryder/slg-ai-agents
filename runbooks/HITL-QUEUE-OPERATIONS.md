# Runbook — HITL Approval Queue Operations

The human-approval gate is the control that lets a government deploy a *writing* agent. This runbook keeps it healthy.

## What lands in the queue
Any high-risk tool attempt (`HIGH_RISK_TOOLS` in `policy.py`) — create/update a 311 case, book an appointment, assemble a FOIA package, draft a notice, route a permit, run a runbook. The agent pauses (`interrupt_before=[human_review_gate]` / Step Functions `waitForTaskToken`) and writes a pending record to the HITL table.

## Reviewer SLAs (tune per program)
| Class | Target |
|---|---|
| Resident-impacting (notice, request) | 1 business day |
| Records release prep | per statutory clock |
| IT runbook | 1 hour (P1/P2) |

## Daily checks
1. **Queue depth** (CloudWatch metric) — alarm if > threshold; pull in reviewers.
2. **Approval latency** — rising latency = staffing or training gap.
3. **Reject reasons** — recurring rejects feed prompt/eval improvements.
4. **Audit completeness** — every ALLOW after a high-risk attempt must carry an `approved_by.sub` (verified in `test_high_risk_proceeds_with_valid_approval`).

## Failure modes
- **Stuck task token** → the durable checkpointer (DynamoDB saver) lets a suspended gate survive restart; resume with `SendTaskSuccess`.
- **Reviewer identity missing** → the gateway refuses to execute (fail-closed); never patch by bypassing the gate.
