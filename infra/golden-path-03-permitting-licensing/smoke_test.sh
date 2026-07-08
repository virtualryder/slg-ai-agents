#!/usr/bin/env bash
# Golden-path smoke test (fails loudly): start an execution, approve the human gate with a REAL
# bound approval, and assert the workflow finished through the governed gateway (not BLOCKED).
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-03-dev}"
REGION="${AWS_REGION:-us-east-1}"
# must match the stack's TokenSecret so the reviewer-minted approval verifies in finalize
export APPROVAL_TOKEN_SECRET="${APPROVAL_TOKEN_SECRET:-${TOKEN_SECRET:-}}"
[ -n "$APPROVAL_TOKEN_SECRET" ] || { echo "FAIL: set TOKEN_SECRET (or APPROVAL_TOKEN_SECRET) to the stack's TokenSecret parameter before running the smoke test."; exit 1; }

SM_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" --output text)
[ -n "$SM_ARN" ] || { echo "FAIL: no StateMachineArn output on $STACK"; exit 1; }
echo "State machine: $SM_ARN"

INPUT=$(cat ../../aws-native-reference/03-permitting-licensing/sample_input.json)
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input "$INPUT" --region "$REGION" --query executionArn --output text)
echo "Started: $EXEC_ARN"

echo "==> waiting for the human gate…"
TOKEN=""
for i in $(seq 1 30); do
  TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
    --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text 2>/dev/null | \
    grep -o '"Token":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
  [ -n "$TOKEN" ] && break; sleep 2
done
[ -n "$TOKEN" ] || { echo "FAIL: human-gate task token never appeared"; exit 1; }

echo "==> reviewer mints a BOUND approval (separation of duties) and approves"
APPROVAL=$(python3 mint_approval.py)
aws stepfunctions send-task-success --task-token "$TOKEN" --region "$REGION" --task-output "$APPROVAL"

STATUS="RUNNING"
for i in $(seq 1 30); do
  STATUS=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query status --output text)
  [ "$STATUS" != "RUNNING" ] && break; sleep 2
done
OUT=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query output --output text)
echo "output: $OUT"
CASE=$(printf '%s' "$OUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('case_status',''))" 2>/dev/null || echo "")

if [ "$STATUS" = "SUCCEEDED" ] && { [ "$CASE" = "ACTION_COMPLETED" ] || [ "$CASE" = "COMPLETED" ]; }; then
  echo "PASS: case_status=$CASE — workflow completed through the governed gateway."
  exit 0
fi
echo "FAIL: status=$STATUS case_status=$CASE"
exit 1
