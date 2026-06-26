# Golden Path — 05 Public Records & FOIA (one command)

Same wired pattern as the 311 reference (`infra/golden-path-311/`), applied to **Public Records & FOIA**.
Deploys the real agent: shared layer (platform_core + governance + this agent's `core.py`), the
five workflow Lambdas (classify → draft → check → **human gate** (`waitForTaskToken`) → finalize),
the governed connector, the real Step Functions ASL
(`aws-native-reference/05-public-records-foia/stepfunctions/05_public_records_foia.asl.json`), an HTTP API with a Cognito JWT authorizer +
access logging + throttling, per-function least-privilege roles, a Bedrock Guardrail
(prompt-attack in+out), hardened Cognito, and an audit table.

```bash
cd infra/golden-path-05-public-records-foia
./deploy.sh slg-05-dev          # sam build && sam deploy
./smoke_test.sh slg-05-dev      # start execution → approve human gate → assert outcome
./destroy.sh slg-05-dev         # sam delete
```
Prereqs: AWS SAM CLI, account credentials, Bedrock model access. See the 311 guide
(`infra/golden-path-311/DEPLOY-GOLDEN-PATH.md`) for the full control walk-through, and
`docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` for verification status.
