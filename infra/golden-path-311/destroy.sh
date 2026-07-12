#!/usr/bin/env bash
# Tear down the golden-path stack. (Audit table has PITR; export any evidence first.)
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-311-dev}"
REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${STACK#slg-311-}"; ENVIRONMENT="${ENVIRONMENT:-dev}"

# Stop any executions still paused at the human gate FIRST — a RUNNING execution keeps the state
# machine (and thus the whole stack delete) IN_PROGRESS for a long time.
SM_ARN=$(aws stepfunctions list-state-machines --region "$REGION" \
  --query "stateMachines[?name=='$STACK'].stateMachineArn" --output text 2>/dev/null || true)
if [ -n "$SM_ARN" ] && [ "$SM_ARN" != "None" ]; then
  for E in $(aws stepfunctions list-executions --state-machine-arn "$SM_ARN" --status-filter RUNNING \
      --region "$REGION" --query "executions[*].executionArn" --output text 2>/dev/null); do
    aws stepfunctions stop-execution --execution-arn "$E" --region "$REGION" >/dev/null 2>&1 \
      && echo "stopped running execution $E" || true
  done
fi

sam delete --stack-name "$STACK" --region "$REGION" --no-prompts || true

# Remove the retained tables (fixed names) so re-deploy is clean (no EarlyValidation collision).
for T in "slg-311-${ENVIRONMENT}-audit" "slg-311-${ENVIRONMENT}-pending-approvals"; do
  aws dynamodb delete-table --table-name "$T" --region "$REGION" >/dev/null 2>&1 \
    && echo "removed retained table $T" || true
done
echo "Deleted $STACK and its retained tables."
