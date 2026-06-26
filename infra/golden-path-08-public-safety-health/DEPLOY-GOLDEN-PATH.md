# Golden Path — 08 Public Safety & Public Health (one command)

Same wired pattern as the 311 reference (`infra/golden-path-311/`), applied to **Public Safety & Public Health**.
Deploys the real agent: shared layer (platform_core + governance + this agent's `core.py`), the
five workflow Lambdas (classify → draft → check → **human gate** (`waitForTaskToken`) → finalize),
the governed connector, the real Step Functions ASL
(`aws-native-reference/08-public-safety-health/stepfunctions/08_public_safety_health.asl.json`), an HTTP API with a Cognito JWT authorizer +
access logging + throttling, per-function least-privilege roles, a Bedrock Guardrail
(prompt-attack in+out), hardened Cognito, and an audit table.

```bash
cd infra/golden-path-08-public-safety-health
./deploy.sh slg-08-dev          # sam build && sam deploy
./smoke_test.sh slg-08-dev      # start execution → approve human gate → assert outcome
./destroy.sh slg-08-dev         # sam delete
```
Prereqs: AWS SAM CLI, account credentials, Bedrock model access. See the 311 guide
(`infra/golden-path-311/DEPLOY-GOLDEN-PATH.md`) for the full control walk-through, and
`docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` for verification status.
