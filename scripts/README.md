# Scripts
- `build_lambdas.sh <agent-id>` — vendors `platform_core` + `governance` and zips the agent's connector + native Lambdas.
- `deploy.sh <agent-id> <env> <gateway-mode> <deploy-mode>` — stages templates to S3 and deploys the `quickstart.yaml` master stack into a new account.
