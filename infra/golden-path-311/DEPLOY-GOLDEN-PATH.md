# Golden Path — 01 Resident Services / 311 (fully wired, one command)

This is the **deployable reference** the README points to. Unlike the generic
`infra/cloudformation/quickstart.yaml` (baseline scaffolding + placeholder state machine),
this SAM application deploys the **real agent** end to end and is the template the other
seven agents inherit from.

## What it deploys
- **Shared layer** — `platform_core` (deny-by-default MCP gateway, PII masker, tokens, audit) + `governance` (grounding) + the agent `core.py`, assembled by `layer/Makefile`.
- **Five workflow Lambdas** — `classify → draft → check → finalize`, plus `hitl_notify` for the human gate. Each has its **own least-privilege role** (`draft` → `bedrock:InvokeModel` on the model ARN only; `check` → `bedrock:ApplyGuardrail` on the guardrail ARN only; `finalize` → `dynamodb:PutItem` on the audit table only).
- **Governed connector Lambda** — the single backend a gateway target invokes.
- **Real Step Functions state machine** — from `aws-native-reference/01-resident-services-311/stepfunctions/resident_services.asl.json`, with the **human gate** implemented as `waitForTaskToken`. Execution + logging configured.
- **HTTP API gateway** — Cognito **JWT authorizer**, **access logging** to CloudWatch, and **throttling** (burst/rate parameters). Route `POST /tool/{kind}/{method}` → connector.
- **Bedrock Guardrail** — prompt-attack on **input AND output**, PII block/anonymize, denied-topic.
- **Cognito** — admin-create, **MFA on**, advanced security **ENFORCED**, 14-char password policy, 15-minute access/ID tokens, **immutable** `slg_role` claim.
- **Audit table** — DynamoDB with PITR + SSE. *(Append-only enforcement — conditional writes + Update/Delete deny — and data-class-driven WORM land in P2.)*

## Deploy (one command path)
```bash
cd infra/golden-path-311
./deploy.sh slg-311-dev          # = sam build && sam deploy
./smoke_test.sh slg-311-dev      # start execution → approve human gate → assert outcome
./destroy.sh slg-311-dev         # sam delete
```
Prereqs: AWS SAM CLI, account credentials, and Bedrock model access enabled for `BedrockModelId`.

## How the smoke test proves the path
It starts an execution with `sample_input.json`, waits for the **human gate** (`waitForTaskToken`),
sends `SendTaskSuccess` with a reviewer approval, and asserts the execution `SUCCEEDED` with a
non-`BLOCKED_NO_APPROVAL` `case_status` — i.e. the consequential write only happened **after** a
human approved. Run it without approving and `finalize` returns `BLOCKED_NO_APPROVAL`, proving the
gate is enforced in code, not just described.

## Verification status
- `cfn-lint` clean (SAM transform). See `docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` (P1).
- Live deploy + smoke test run **in the customer/SA account** — not executed in this repo's CI
  (no account). The scripts above are the exact steps.

## What still differs from production (tracked in P2)
Append-only audit enforcement, full IAM permissions-boundaries, WAF on the gateway, egress
allowlisting, Cognito enterprise federation, and the AgentCore-Identity/STS token swap. See the
remediation plan.
