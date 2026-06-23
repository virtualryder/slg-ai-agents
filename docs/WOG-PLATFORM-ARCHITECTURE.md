# Whole-of-Government Orchestration Platform — Reference Architecture


> **The WoG platform is additive, not a prerequisite.** Every agent deploys standalone with its own VPC, KMS, WORM audit, gateway, and human gate (`docs/DEPLOYMENT-MODELS.md`). Adopt this orchestration layer agent-by-agent when ready; the same agents become saga steps with no rewrite.


## The problem this layer solves
The obstacle to whole-of-government service is **not the model**. It is identity, consent, interagency data-sharing, incompatible systems, and *which agency has the authority to act*. A resident who moves should not have to understand which of a DMV, a 311 CRM, an elections office, and a sanitation department owns each sub-task. This platform organizes services around the **life event**, coordinates the agencies, and keeps a single compliance record — without any agency surrendering control of its system of record.

## The five pillars → AWS services
```
┌── GOVERN TOOL ACCESS ────────────────────────────────────────────────┐
│  Per-tool contract: agency · purposes · data classes · residency ·    │
│  read/write · transaction threshold · idempotency · rollback · audit  │
│  AWS: AgentCore Gateway targets + Amazon Verified Permissions (Cedar)  │
│       for purpose/threshold/residency; STS scoped tokens               │
├── CANONICAL DATA LAYER ──────────────────────────────────────────────┤
│  One Resident/Address/Case contract; agency adapters at the boundary  │
│  AWS: Glue Data Catalog + DataZone (ownership) + Lake Formation (ACL) │
├── WORKFLOW COORDINATION (SAGA) ──────────────────────────────────────┤
│  Forward + compensation per step; consent+confirmation gates;         │
│  idempotency; automatic rollback on failure                           │
│  AWS: Step Functions (durable, Catch→compensate) + Lambda; A2A        │
├── COMPLIANCE EVENTS + EVIDENCE ──────────────────────────────────────┤
│  Immutable masked events; case-level evidence; retention by data class│
│  AWS: EventBridge (routing) + DynamoDB append-only + S3 Object Lock   │
├── IDENTITY & CONSENT ────────────────────────────────────────────────┤
│  AAL-gated, scoped, time-bound consent ledger                         │
│  AWS: Cognito / Identity Center (federation) + DynamoDB consent store │
└──────────────────────────────────────────────────────────────────────┘
                         every write still passes ↓
              slg_agent_platform MCP gateway (deny-by-default,
              agent grant ∩ user entitlement, scoped token, audit)
```

## Why the saga (not a distributed transaction)
There is no two-phase commit across a DMV, an HHS eligibility system, and a 311 CRM. The saga pattern gives **eventual consistency with explicit compensation**: each step records how to undo itself, and a downstream failure triggers reverse-order rollback. The constituent is never left half-enrolled — and the compliance trail records both the commit and the undo.

## Safety invariants (all tested)
1. **No cross-agency authority concentration** — the orchestrator and saga coordinator hold no tool grants; every write flows through a specialist's gateway path.
2. **Purpose binding** — a benefits tool used for a fraud sweep is a *different, separately consented* purpose and is denied without it.
3. **Consent + confirmation before material action** — fail-closed; the saga pauses (it does not silently proceed) until satisfied.
4. **Exactly-once** — idempotency keys make retries/resumes safe.
5. **Residency** — a `us-gov` tool cannot execute in a `us` deployment boundary (and vice-versa).
6. **Retention by data class** — the binding retention is the max across all data classes the case touched.

## How specialist agents plug in
Each agent (01–08) is a saga step `forward` action (or a registered supervisor handler). Adding an agency is a new `AgencyAdapter` + governed-catalog entries — no change to the orchestrator. This is what lets a state grow from one life-event to many on one governed substrate.
