#!/usr/bin/env bash
# SECURE golden-path smoke test (fails loudly). Proves the CloudFront+WAF edge is the only
# door AND that the governed human gate still holds:
#   1) probe THROUGH CloudFront (WAF + injected X-Origin-Verify header)   -> 200
#   2) probe the DIRECT execute-api URL without the origin header         -> 401/403 (cloaked)
#   3) negative control: approve the human gate WITHOUT a valid approval  -> write BLOCKED
#   4) positive control (base assertion): reviewer-minted bound approval  -> workflow completes
#      (step 4 reads the stack's in-stack token-signing secret automatically)
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-08-secure-dev}"
REGION="${AWS_REGION:-us-east-1}"

out() {
  aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

CF_DOMAIN=$(out CloudFrontDomain)
GW_URL=$(out GatewayUrl)
{ [ -n "$CF_DOMAIN" ] && [ -n "$GW_URL" ]; } || { echo "FAIL: missing CloudFrontDomain/GatewayUrl outputs on $STACK"; exit 1; }

echo "==> 1) edge probe through CloudFront: https://${CF_DOMAIN}/edge-health"
CODE=000
for i in $(seq 1 20); do  # a fresh distribution can take a few minutes to deploy globally
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://${CF_DOMAIN}/edge-health" || echo 000)
  [ "$CODE" = "200" ] && break
  sleep 15
done
[ "$CODE" = "200" ] || { echo "FAIL: CloudFront edge probe returned $CODE (want 200)"; exit 1; }
echo "    PASS: 200 via CloudFront (WAF passed, X-Origin-Verify injected at the origin)."

echo "==> 2) direct execute-api probe WITHOUT X-Origin-Verify: ${GW_URL}/edge-health"
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "${GW_URL}/edge-health" || echo 000)
case "$CODE" in
  401|403) echo "    PASS: direct call rejected ($CODE) - origin cloaking works." ;;
  *) echo "FAIL: direct execute-api call returned $CODE (want 401/403) - the API is reachable around CloudFront/WAF"; exit 1 ;;
esac
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -X POST -d '{}' "${GW_URL}/tool/probe/probe" || echo 000)
case "$CODE" in
  401|403) echo "    PASS: direct /tool call rejected ($CODE) (JWT authorizer + origin check)." ;;
  *) echo "FAIL: direct /tool call returned $CODE (want 401/403)"; exit 1 ;;
esac

echo "==> 3) negative control: approve the human gate WITHOUT a valid bound approval"
SM_ARN=$(out StateMachineArn)
[ -n "$SM_ARN" ] || { echo "FAIL: no StateMachineArn output on $STACK"; exit 1; }
INPUT=$(cat ../../aws-native-reference/08-public-safety-health/sample_input.json)
EXEC_ARN=$(aws stepfunctions start-execution --state-machine-arn "$SM_ARN" \
  --input "$INPUT" --region "$REGION" --query executionArn --output text)
TOKEN=""
for i in $(seq 1 30); do
  TOKEN=$(aws stepfunctions get-execution-history --execution-arn "$EXEC_ARN" --region "$REGION" \
    --query "events[?type=='TaskScheduled'].taskScheduledEventDetails.parameters" --output text 2>/dev/null | \
    grep -o '"Token":"[^"]*"' | head -1 | cut -d'"' -f4 || true)
  [ -n "$TOKEN" ] && break; sleep 2
done
[ -n "$TOKEN" ] || { echo "FAIL: human-gate task token never appeared"; exit 1; }
aws stepfunctions send-task-success --task-token "$TOKEN" --region "$REGION" \
  --task-output '{"token":"","reviewer":{"sub":"smoke-no-approval"}}'
STATUS="RUNNING"
for i in $(seq 1 30); do
  STATUS=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query status --output text)
  [ "$STATUS" != "RUNNING" ] && break; sleep 2
done
OUT=$(aws stepfunctions describe-execution --execution-arn "$EXEC_ARN" --region "$REGION" --query output --output text 2>/dev/null || echo "{}")
CASE=$(printf '%s' "$OUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('case_status',''))" 2>/dev/null || echo "")
if [ "$STATUS" = "FAILED" ] || [[ "$CASE" == BLOCKED* ]]; then
  echo "    PASS: write blocked without a valid approval (status=$STATUS case_status=${CASE:-n/a})."
else
  echo "FAIL: unapproved write was NOT blocked (status=$STATUS case_status=$CASE)"; exit 1
fi

echo "==> 4) positive control: base golden-path smoke test (reviewer-minted bound approval)"
../golden-path-08-public-safety-health/smoke_test.sh "$STACK"

echo "PASS: secure smoke test complete for $STACK."
