#!/usr/bin/env bash
# One-command secure combined deploy: secure baseline (VPC/KMS/WORM/edge) + the full 04-benefits-caseworker app.
# Deploy in us-east-1 (the CloudFront-scoped WAF must live in us-east-1).
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-04-secure-dev}"
REGION="${AWS_REGION:-us-east-1}"
[ "$REGION" = "us-east-1" ] || { echo "FAIL: deploy the secure variant in us-east-1 (CloudFront WAF scope). AWS_REGION=$REGION"; exit 1; }
# Token-signing secret is now generated IN-STACK (AWS::SecretsManager::Secret) and resolved
# into the token env vars via a dynamic reference - nothing to pass or generate here.
# smoke_test.sh reads it back from the TokenSecretArn stack output.
# OriginVerifySecret has no template default: CloudFront injects it toward the origin as the
# X-Origin-Verify header and the API rejects requests without it (origin cloaking).
ORIGIN_VERIFY_SECRET="${ORIGIN_VERIFY_SECRET:-}"
if [ -z "$ORIGIN_VERIFY_SECRET" ]; then
  ORIGIN_VERIFY_SECRET="$(openssl rand -hex 32)"
  echo "NOTICE: ORIGIN_VERIFY_SECRET was not set - generated a random origin-cloaking secret (value not shown)."
fi
sam build
sam deploy --stack-name "$STACK" --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --resolve-s3 --no-confirm-changeset \
  --parameter-overrides "OriginVerifySecret=$ORIGIN_VERIFY_SECRET"
aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs" --output table
