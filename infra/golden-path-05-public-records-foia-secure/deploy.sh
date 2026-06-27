#!/usr/bin/env bash
# One-command secure combined deploy: secure baseline (VPC/KMS/WORM/edge) + the full 05-public-records-foia app.
# Deploy in us-east-1 (the CloudFront-scoped WAF must live in us-east-1).
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-05-secure-dev}"
REGION="${AWS_REGION:-us-east-1}"
[ "$REGION" = "us-east-1" ] || { echo "FAIL: deploy the secure variant in us-east-1 (CloudFront WAF scope). AWS_REGION=$REGION"; exit 1; }
sam build
sam deploy --stack-name "$STACK" --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --resolve-s3 --no-confirm-changeset \
  --parameter-overrides "TokenSecret=${APPROVAL_TOKEN_SECRET:-dev-only-not-for-production}"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs" --output table
