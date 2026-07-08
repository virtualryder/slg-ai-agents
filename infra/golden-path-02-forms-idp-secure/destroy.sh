#!/usr/bin/env bash
# Tear down the SECURE golden-path stack, verify it is gone, then explicitly clean up the
# resources the template RETAINS on delete (DeletionPolicy: Retain): the audit table, the
# pending-approvals table, the Cognito user pool (retained pools have survived teardown in
# past validations - delete them explicitly), and the WORM evidence bucket. The WORM bucket
# may legitimately refuse deletion while S3 Object-Lock (COMPLIANCE) retention is active.
# Set KEEP_RETAINED=1 to keep the retained evidence/resources (stack delete only).
set -euo pipefail
cd "$(dirname "$0")"
STACK="${1:-slg-02-secure-dev}"
REGION="${AWS_REGION:-us-east-1}"
KEEP_RETAINED="${KEEP_RETAINED:-0}"

out() {
  aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text 2>/dev/null || true
}

# capture the retained physical resources BEFORE the stack record disappears
AUDIT_TABLE=$(out AuditTableName)
PENDING_TABLE=$(out PendingApprovalsTableName)
USER_POOL=$(out UserPoolId)
WORM_BUCKET=$(out WormBucketName)

sam delete --stack-name "$STACK" --region "$REGION" --no-prompts

echo "==> verifying stack deletion"
ST=""
for i in $(seq 1 60); do
  ST=$(aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
    --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo GONE)
  [ "$ST" = "GONE" ] && break
  [ "$ST" = "DELETE_FAILED" ] && { echo "FAIL: stack delete failed - inspect the CloudFormation events for $STACK"; exit 1; }
  sleep 10
done
[ "$ST" = "GONE" ] || { echo "FAIL: stack $STACK still present (status=$ST)"; exit 1; }
echo "    stack $STACK deleted."

if [ "$KEEP_RETAINED" = "1" ]; then
  echo "KEEP_RETAINED=1 - leaving the retained resources in place:"
  echo "  audit table:             ${AUDIT_TABLE:-<unknown>}"
  echo "  pending-approvals table: ${PENDING_TABLE:-<unknown>}"
  echo "  Cognito user pool:       ${USER_POOL:-<unknown>}"
  echo "  WORM evidence bucket:    ${WORM_BUCKET:-<unknown>}"
  exit 0
fi

echo "==> cleaning up resources retained by DeletionPolicy: Retain"
if [ -n "$AUDIT_TABLE" ] && [ "$AUDIT_TABLE" != "None" ]; then
  if aws dynamodb delete-table --table-name "$AUDIT_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "    deleted audit table $AUDIT_TABLE (export audit evidence beforehand if you needed it)"
  else
    echo "    NOTE: audit table $AUDIT_TABLE not deleted (already gone?) - verify manually"
  fi
fi
if [ -n "$PENDING_TABLE" ] && [ "$PENDING_TABLE" != "None" ]; then
  if aws dynamodb delete-table --table-name "$PENDING_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "    deleted pending-approvals table $PENDING_TABLE"
  else
    echo "    NOTE: pending-approvals table $PENDING_TABLE not deleted (already gone?) - verify manually"
  fi
fi
if [ -n "$USER_POOL" ] && [ "$USER_POOL" != "None" ]; then
  if aws cognito-idp delete-user-pool --user-pool-id "$USER_POOL" --region "$REGION" >/dev/null 2>&1; then
    echo "    deleted Cognito user pool $USER_POOL (retained pools have leaked in past teardowns)"
  else
    echo "    NOTE: Cognito user pool $USER_POOL not deleted - delete it manually"
  fi
fi
if [ -n "$WORM_BUCKET" ] && [ "$WORM_BUCKET" != "None" ]; then
  if aws s3 rb "s3://$WORM_BUCKET" --force >/dev/null 2>&1; then
    echo "    deleted WORM bucket $WORM_BUCKET"
  else
    echo "    NOTE: WORM bucket $WORM_BUCKET not deleted - S3 Object-Lock (COMPLIANCE) retention"
    echo "          blocks removing locked evidence until retention expires; empty + delete it then."
  fi
fi
echo "Teardown of $STACK complete."
