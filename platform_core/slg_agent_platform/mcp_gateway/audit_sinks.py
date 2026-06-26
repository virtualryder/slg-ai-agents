"""
Append-only audit sinks — make tamper-evidence a property of the WRITE PATH,
not just a comment in a CloudFormation template.

The reviewer correctly noted the DynamoDB audit table enabled PITR + KMS but did
NOT enforce append-only: nothing stopped an overwrite (PutItem onto an existing
key) or an UpdateItem/DeleteItem. This module supplies the enforcement primitive:

  * AppendOnlyStore       — in-memory, rejects any overwrite of an existing
                            audit_id (unit-testable model of the control).
  * DynamoDBAppendOnlySink — writes with ConditionExpression
                            `attribute_not_exists(audit_id)` so a duplicate or
                            overwrite is rejected by DynamoDB itself, and NEVER
                            calls UpdateItem/DeleteItem.

Defense in depth (deployed in IaC, see infra/cloudformation/data.yaml):
  * the audit-WRITER IAM role is granted dynamodb:PutItem ONLY (no Update/Delete),
  * an Organizations SCP denies UpdateItem/DeleteItem on the audit table to all,
  * finalized snapshots are exported to S3 Object Lock (WORM).
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class AppendOnlyViolation(Exception):
    """Raised when a write would overwrite or mutate an existing audit record."""


class AppendOnlyStore:
    """In-memory append-only store: first write of an audit_id wins; no overwrite, no delete."""

    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def put(self, record: Dict[str, Any]) -> str:
        audit_id = record.get("audit_id")
        if not audit_id:
            raise AppendOnlyViolation("audit record requires an audit_id")
        if audit_id in self._items:
            raise AppendOnlyViolation(f"append-only: {audit_id} already written")
        self._items[audit_id] = dict(record)
        return audit_id

    # Intentionally NO update() or delete() — mutation is not part of the contract.
    def get(self, audit_id: str) -> Optional[Dict[str, Any]]:
        return self._items.get(audit_id)

    def __len__(self) -> int:
        return len(self._items)


class DynamoDBAppendOnlySink:  # pragma: no cover - requires boto3 + AWS
    """Production sink: conditional PutItem only. Overwrite/replay -> ConditionalCheckFailed."""

    def __init__(self, table_name: str, client: Any = None) -> None:
        import boto3  # local import so the module imports without boto3 in dev
        self._table = (client or boto3.resource("dynamodb")).Table(table_name)

    def put(self, record: Dict[str, Any]) -> str:
        from botocore.exceptions import ClientError
        try:
            self._table.put_item(
                Item=record,
                ConditionExpression="attribute_not_exists(audit_id)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AppendOnlyViolation("append-only: record already exists") from exc
            raise
        return record["audit_id"]
