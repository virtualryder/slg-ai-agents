#!/usr/bin/env bash
# Golden path: build + deploy the fully wired 311 agent.
# Prereqs: AWS SAM CLI, credentials for the target account, Bedrock model access enabled.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-311-dev}"
REGION="${AWS_REGION:-us-east-1}"

# Token-signing secret is now generated IN-STACK (AWS::SecretsManager::Secret) and resolved
# into the token env vars via a dynamic reference - nothing to pass or generate here.
# smoke_test.sh reads it back from the TokenSecretArn stack output.

echo "==> stage shared layer (platform_core + governance + core.py)"
bash prepare_layer.sh    # Windows without a bash shell: run prepare_layer.sh's three copies by hand, or use Git Bash

echo "==> sam build"
sam build

echo "==> sam deploy (stack: $STACK, region: $REGION)"
sam deploy \
  --stack-name "$STACK" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --parameter-overrides "Environment=dev ConnectorMode=fixture"

echo "==> outputs"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
