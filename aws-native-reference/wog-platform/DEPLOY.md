# WoG Saga — AWS-native deploy (Step Functions + Lambda, live on DynamoDB + EventBridge)

The life-event saga is a **generic** state machine (`stepfunctions/lifeevent_saga.asl.json`)
that runs ANY life-event by passing its declarative step list as input. The step
list is built from `gov_platform/wog_orchestration/saga/life_events.py` — the same
templates the in-process coordinator uses (moving · job_loss · new_business ·
disaster · bereavement).

## Lambdas (Task bodies)
| Lambda | Role | State |
|---|---|---|
| `gate.handler` | consent + explicit-confirmation gate | `Gate` (use `waitForTaskToken` in prod to pause for the reviewer/resident) |
| `step.handler` | one governed write + DynamoDB idempotency + committed event | `Step` |
| `compensate.handler` | reverse-order rollback of committed compensable steps | `Compensate` (top-level `Catch`) |

At cold start each Lambda calls `_shared.bootstrap()`. With `WOG_BACKEND=aws` it wires:
- **Consent** → DynamoDB `slg-wog-consent-<env>` (`AwsConsentStore`)
- **Events** → DynamoDB `slg-wog-events-<env>` + **EventBridge** `slg-wog-compliance-<env>` (`AwsComplianceEventBus`)
- **Idempotency** → DynamoDB `slg-wog-idempotency-<env>` conditional put (`AwsIdempotencyStore`, exactly-once across invocations)
- **Governed writes** → `GovernedToolGateway` → MCP gateway (deny-by-default)

## Deploy into an account
```bash
# 1. Package the Lambdas (vendors platform_core + gov_platform + governance)
scripts/build_lambdas.sh wog-platform
aws s3 cp .build/wog-platform-lambdas.zip s3://$CODE_BUCKET/wog-platform-lambdas.zip

# 2. Deploy the live stack (event bus + consent/event/idempotency DynamoDB +
#    WORM evidence + 3 Lambdas + Step Functions saga)
aws cloudformation deploy --template-file infra/cloudformation/wog-platform.yaml \
  --stack-name slg-wog-dev \
  --parameter-overrides Environment=dev KmsKeyArn=$KMS_ARN \
                        CodeBucket=$CODE_BUCKET CodeKey=wog-platform-lambdas.zip \
                        DeploymentResidency=us \
  --capabilities CAPABILITY_NAMED_IAM

# 3. Seed consent (DynamoDB) for the resident's life-event scopes, then start an execution
aws stepfunctions start-execution --state-machine-arn $SAGA_ARN \
  --input file://execution-input.json   # {event, steps:[...], claims, approval, confirmations, correlation_id, resident_ref}
```
`GatewayMode` note: the saga's governed writes use the portable gateway path, so the
stack deploys in commercial **and** GovCloud regions (`DeploymentResidency=us-gov`).

## Prove it locally first (no AWS, no creds)
```bash
PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py
python -m pytest aws-native-reference/wog-platform/tests -q   # 14 tests
```
The runner emulates the ASL control flow over the REAL Lambda handlers: all five
life-events complete, a forced outage compensates, a missing confirmation pauses.
`WOG_BACKEND=memory` (default locally) swaps the AWS stores for in-process ones —
handler code is identical.
