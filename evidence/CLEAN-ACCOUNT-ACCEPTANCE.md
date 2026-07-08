# Clean-Account Acceptance Report — SLG AI Agents (8 golden paths)

Sanitized deployment evidence for the live validation claimed in the README
(§Deployed & validated). Validation account ID and IAM user are redacted; raw CLI JSON is
available on request. All verification queries were read-only.

**Account:** `<VALIDATION-ACCOUNT-ID>` · **Region:** us-east-1 · **Run date:** 2026-06-30 (UTC) · **Independently re-verified:** 2026-07-07 via AWS CLI.

## 1. Stack lifecycle — all 8 golden paths

Deployed via SAM (CloudTrail shows `ExecuteChangeSet` events, the SAM deploy mechanism), reached
CREATE_COMPLETE, and were deleted the same session:

| Stack (actual name) | ExecuteChangeSet (UTC) | DeleteStack (UTC) |
|---|---|---|
| slg-311-deploytest | Jun 30 00:32 / 00:36 / 00:41 | Jun 30 00:34 / 00:47 |
| slg-02-deploytest … slg-08-deploytest (7 stacks) | Jun 30 00:43 (parallel) | Jun 30 00:47 (parallel) |

> Naming note: the deployed stacks used the `-deploytest` suffix (deploy-script parameter), not the
> `slg-*-dev` defaults shown in some docs. The suffix difference does not affect the templates used.

## 2. Runtime verification

Step Functions `StartExecution` CloudTrail events during the deploy window confirm workflows were
run, not just provisioned (311 Classify→Retrieve→Draft→Check→human-gate pause; agent 04 cross-check;
append-only audit writes observed via smoke tests). Two real defects were found only by the live
run and fixed (Guardrail `PROMPT_ATTACK` output strength; Lambda `parents[3]` IndexError) — see
CHANGELOG.

## 3. Teardown verification

Post-run and re-verified 2026-07-07: zero `slg-*` CloudFormation stacks, DynamoDB tables, Cognito
user pools, Bedrock guardrails, Lambda functions, or Step Functions state machines remain. Only the
shared SAM artifact bucket (`aws-sam-cli-managed-default-*`) persists, as expected for SAM tooling.

## 4. Security-control notes from this validation cycle

- `TokenSecret` no longer has a development default in any of the 16 templates (required NoEcho
  parameter, MinLength 32; deploy scripts generate one via `openssl rand -hex 32` if unset).
- The audit-sink append-only property for this suite is enforced at the application layer and
  negative-tested offline (`test_audit_append_only.py`); the IAM-layer Update/Delete explicit deny
  was proven live in the Aegis platform repo (Runs 1 and 10) on the same control pattern.

## 5. Method

Read-only CLI: `cloudformation list-stacks`, `cloudtrail lookup-events` (ExecuteChangeSet /
DeleteStack / StartExecution), `dynamodb list-tables`, `cognito-idp list-user-pools`.
Portfolio-level export: `Projects-DR/evidence/AWS-CLEAN-ACCOUNT-EVIDENCE-2026-07-07.md`
(kept outside the repo).
