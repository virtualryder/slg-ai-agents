# Golden Path — 04 Benefits & HHS Caseworker (one command)

Same wired pattern as the 311 reference (`infra/golden-path-311/`), applied to **Benefits & HHS Caseworker**.
Deploys the real agent: shared layer (platform_core + governance + this agent's `core.py`), the
five workflow Lambdas (classify → draft → check → **human gate** (`waitForTaskToken`) → finalize),
the governed connector, the real Step Functions ASL
(`aws-native-reference/04-benefits-caseworker/stepfunctions/04_benefits_caseworker.asl.json`), an HTTP API with a Cognito JWT authorizer +
access logging + throttling, per-function least-privilege roles, a Bedrock Guardrail
(prompt-attack in+out), hardened Cognito, and an audit table.

```bash
cd infra/golden-path-04-benefits-caseworker
./deploy.sh slg-04-dev          # sam build && sam deploy
./smoke_test.sh slg-04-dev      # start execution → approve human gate → assert outcome
./destroy.sh slg-04-dev         # sam delete
```
Prereqs: AWS SAM CLI, account credentials, Bedrock model access. See the 311 guide
(`infra/golden-path-311/DEPLOY-GOLDEN-PATH.md`) for the full control walk-through, and
`docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` for verification status.
