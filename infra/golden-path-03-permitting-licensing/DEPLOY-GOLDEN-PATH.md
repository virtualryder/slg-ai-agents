# Golden Path — 03 Permitting & Licensing (one command)

Same wired pattern as the 311 reference (`infra/golden-path-311/`), applied to **Permitting & Licensing**.
Deploys the real agent: shared layer (platform_core + governance + this agent's `core.py`), the
five workflow Lambdas (classify → draft → check → **human gate** (`waitForTaskToken`) → finalize),
the governed connector, the real Step Functions ASL
(`aws-native-reference/03-permitting-licensing/stepfunctions/03_permitting_licensing.asl.json`), an HTTP API with a Cognito JWT authorizer +
access logging + throttling, per-function least-privilege roles, a Bedrock Guardrail
(prompt-attack in+out), hardened Cognito, and an audit table.

```bash
cd infra/golden-path-03-permitting-licensing
./deploy.sh slg-03-dev          # sam build && sam deploy
./smoke_test.sh slg-03-dev      # start execution → approve human gate → assert outcome
./destroy.sh slg-03-dev         # sam delete
```
Prereqs: AWS SAM CLI, account credentials, Bedrock model access. See the 311 guide
(`infra/golden-path-311/DEPLOY-GOLDEN-PATH.md`) for the full control walk-through, and
`docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` for verification status.
