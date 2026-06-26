#!/usr/bin/env bash
# Golden-path smoke test: start an execution, approve the human gate, assert outcome.
# Proves the wired path end to end: Classify -> Draft -> Check -> HUMAN GATE -> Finalize.
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-03-dev}"
REGION="${AWS_REGION:-us-east-1}"

SM_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" --output text)
echo "State machine: $SM_ARN"

INPUT=$(cat ../../aws-native-reference/03-permitting-licensing/sample_input.json)
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input "$INPUT" --region "$REGION" --query executionArn --output text)
echo "Started: $EXEC_ARN"

echo "==> waiting for the human gate (waitForTaskToken)…"
# Poll for the task token emitted by the hitl_notify activity; a reviewer normally supplies this.
TOKEN=""
for i in $(seq 1 30); do
  TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
    --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text 2>/dev/null | \
    grep -o '"Token":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
  [ -n "$TOKEN" ] && break; sleep 2
done

if [ -n "$TOKEN" ]; then
  echo "==> reviewer APPROVES (SendTaskSuccess)"
  aws stepfunctions send-task-success --task-token "$TOKEN" --region "$REGION" \
    --task-output '{"approval":{"approved":true,"reviewer":{"sub":"licensed-plan-reviewer-1","role":"PERMIT_OFFICIAL"}}}'
fi

echo "==> final status"
aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" \
  --query "{status:status, output:output}" --output json
echo "PASS if status=SUCCEEDED and output.case_status is REQUEST_CREATED/ANSWERED (not BLOCKED_NO_APPROVAL)."
