# Runbook — Disaster Recovery (SLG Governed Agent Platform)
*Scope: recovering an agent and/or the WoG platform after an availability or data-integrity event. The platform is serverless and stateless at the compute layer, so DR is dominated by the **stateful stores** (audit, case state, consent, evidence) — all of which are designed for durability and tamper-evidence.*

## 1. Targets (set per agency / data class)
| Tier | Example | RTO | RPO |
|---|---|---|---|
| Tier-1 (constituent-facing agent) | Resident Services, Benefits intake | ≤ 4 h | ≤ 15 min |
| Tier-2 (back-office agent) | Procurement, Records | ≤ 8 h | ≤ 1 h |
| Audit / evidence | append-only audit, WORM records | **no data loss** | 0 (immutable) |

## 2. What is stateful (and how it's protected)
| Store | Holds | Durability posture |
|---|---|---|
| **DynamoDB — audit** | every gateway decision / compliance event | **PITR** on; deny Update/Delete; optional **global tables** for multi-region |
| **DynamoDB — case/checkpoint, consent, idempotency** | workflow state, consent ledger, exactly-once keys | PITR; global tables for active-passive |
| **S3 Object Lock (WORM)** | finalized records, evidence packages | **versioning + Object Lock (COMPLIANCE)**; **CRR** to a second region |
| **Aurora** (if used for case state) | durable case state / LangGraph checkpoints | Multi-AZ; automated backups; **Aurora Global Database** option |
| **KMS CMK** | encryption keys (per data class) | multi-Region keys where cross-region DR is required |
| **Secrets Manager** | connector credentials | replicated to the DR region; resolved at runtime (no redeploy) |
| **Step Functions** | in-flight saga executions incl. paused human gates | durable; the human gate survives because the checkpoint lives in DynamoDB/Aurora, not memory |

Compute (Lambda, Fargate, Step Functions definitions, the gateway, agents) is **rebuildable from IaC** — there is no stateful compute to recover.

## 3. Failure scenarios & response
**A. AZ failure** — no action: all managed services (DynamoDB, S3, Aurora Multi-AZ, Lambda, Step Functions, ALB) are multi-AZ. Confirm health in CloudWatch.

**B. Accidental deletion / corruption of a record** — the audit table denies Update/Delete and WORM denies overwrite, so the *record of truth* cannot be corrupted. For derived/case state, restore the table via **PITR** to a timestamp before the event; replay is safe because writes are idempotent (idempotency keys).

**C. Region impairment (active-passive)** —
1. Confirm the primary region is impaired (AWS Health Dashboard, CloudWatch).
2. Promote the DR region: DynamoDB **global tables** already replicate; **Aurora Global Database** — promote the secondary; S3 data is present via **CRR**.
3. Re-deploy the stacks in the DR region from IaC (`scripts/deploy.sh <agent> <env> portable <mode>` with `BEDROCK_REGION`/endpoints pointed at the DR region) — minutes, because there's no stateful compute.
4. Repoint CloudFront origin / DNS to the DR API endpoint.
5. Resume paused Step Functions executions (the human-gate checkpoints replicated with the state store).
**Verify:** run the agent's `DEPLOY-RUNBOOK.md` §9 smoke tests in the DR region before taking traffic.

**D. KMS key unavailability** — use the multi-Region key replica in the DR region; data re-encrypts transparently. If a key was disabled in error, re-enable; if scheduled for deletion, cancel within the window.

**E. Bedrock model/region issue** — the LLM factory abstracts the provider/region; switch `BEDROCK_REGION` or fail over to an alternate model tier. Guardrails remain mandatory in the DR region.

## 4. Backups & retention
DynamoDB PITR (35-day window) + on-demand backups before major changes; S3 versioning + Object Lock per the records-retention schedule (default 6–7 yr; tune to schedule); Aurora automated backups + manual snapshots. **WORM retention is a legal control, not just DR** — never shorten it to reclaim space without the records officer's sign-off.

## 5. Test it (game days, quarterly)
1. PITR-restore the case-state table into a scratch table; confirm an in-flight saga resumes.
2. Simulate region failover in a non-prod account; measure actual RTO/RPO against §1.
3. Confirm the human gate survives a forced Step Functions/region interruption.
4. Confirm WORM records are intact and un-overwritable after the drill.
Record results; update RTO/RPO targets and this runbook.
