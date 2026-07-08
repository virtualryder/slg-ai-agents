#!/usr/bin/env bash
# Golden path: build + deploy the fully wired 311 agent.
# Prereqs: AWS SAM CLI, credentials for the target account, Bedrock model access enabled.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-03-dev}"
REGION="${AWS_REGION:-us-east-1}"

# TokenSecret has no template default: generate a strong random one unless provided.
TOKEN_SECRET="${TOKEN_SECRET:-${APPROVAL_TOKEN_SECRET:-}}"
if [ -z "$TOKEN_SECRET" ]; then
  TOKEN_SECRET="$(openssl rand -hex 32)"
  echo "NOTICE: TOKEN_SECRET was not set - generated a random secret for this deployment (value not shown)."
  echo "        Export TOKEN_SECRET before deploying if you need it later (e.g. for smoke_test.sh)."
fi

echo "==> sam build"
sam build

echo "==> sam deploy (stack: $STACK, region: $REGION)"
sam deploy \
  --stack-name "$STACK" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --parameter-overrides "Environment=dev ConnectorMode=fixture TokenSecret=$TOKEN_SECRET"

echo "==> outputs"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
