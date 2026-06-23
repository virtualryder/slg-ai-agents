#!/usr/bin/env bash
# Stage nested templates to S3 and deploy the quickstart master stack to a new account.
# usage: deploy.sh <agent-id> <env> <gateway-mode portable|agentcore> <deploy-mode native|container>
set -euo pipefail
AGENT="${1:?agent-id}"; ENV="${2:-dev}"; GW="${3:-portable}"; DM="${4:-native}"
: "${CFN_BUCKET:?set CFN_BUCKET}"; : "${CODE_BUCKET:?set CODE_BUCKET}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
aws s3 sync "$ROOT/infra/cloudformation" "s3://$CFN_BUCKET/slg" --exclude "README.md"
"$ROOT/scripts/build_lambdas.sh" "$AGENT"
aws s3 cp "$ROOT/.build/$AGENT-lambdas.zip" "s3://$CODE_BUCKET/$AGENT-lambdas.zip"
aws cloudformation deploy --template-file "$ROOT/infra/cloudformation/quickstart.yaml" \
  --stack-name "slg-$AGENT-$ENV" \
  --parameter-overrides AgentId="$AGENT" Environment="$ENV" GatewayMode="$GW" DeployMode="$DM" \
                        TemplateBaseUrl="https://$CFN_BUCKET.s3.amazonaws.com/slg" \
  --capabilities CAPABILITY_NAMED_IAM
echo "deployed slg-$AGENT-$ENV ($GW/$DM)"
