#!/usr/bin/env bash
# Tear down the golden-path stack. (Audit table has PITR; export any evidence first.)
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-06-dev}"
REGION="${AWS_REGION:-us-east-1}"
sam delete --stack-name "$STACK" --region "$REGION" --no-prompts
echo "Deleted $STACK."
