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
- The audit-sink append-only property is now enforced at the IAM layer in every golden-path
  template (explicit `Deny` on `dynamodb:UpdateItem`/`DeleteItem` for the audit table) — proven
  live in the secure-variant deploy below, and independently in the Aegis platform repo (Runs 1, 10).

## 4a. Secure-variant live validation (2026-07-08)

The hardened `golden-path-311-secure` stack (adds a private VPC, CloudFront + WAF edge, Cognito JWT
authorizer, and CloudFront origin cloaking) was deployed to the validation account
(`slg-311-secure-dev`, us-east-1, CREATE_COMPLETE), exercised over HTTPS, and torn down:

| Test | Result | Proves |
|---|---|---|
| `GET` via CloudFront edge (`d13x…cloudfront.net/edge-health`) | **HTTP 200** | Legitimate edge path works (CloudFront injects the `X-Origin-Verify` header) |
| `GET` direct execute-api URL, **no origin header** | **HTTP 403** | **Origin cloaking holds** — the API GW URL cannot be called around CloudFront/WAF |
| `POST` protected `/tool` route, **no JWT** | **HTTP 401** | Cognito JWT authorizer rejects unauthenticated calls |
| IAM simulation, `FinalizeFnRole` vs `slg-311-dev-audit` | `PutItem=allowed`, `UpdateItem/DeleteItem=explicitDeny` | Audit table is append-only at the IAM layer |

Teardown: stack deleted after the run (CloudFront distribution disable + delete). The secure variant
now ships `smoke_test.sh` (which automates the three HTTP assertions above) and `destroy.sh` (which
also cleans the retained audit/approvals tables, Cognito pool, and WORM bucket).

## 5. Method

Read-only CLI: `cloudformation list-stacks`, `cloudtrail lookup-events` (ExecuteChangeSet /
DeleteStack / StartExecution), `dynamodb list-tables`, `cognito-idp list-user-pools`.
Portfolio-level export: `Projects-DR/evidence/AWS-CLEAN-ACCOUNT-EVIDENCE-2026-07-07.md`
(kept outside the repo).
