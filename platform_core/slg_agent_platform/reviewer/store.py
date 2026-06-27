"""Pending-approval store — where a paused human gate parks the request + its task token
until a reviewer acts. Single-use is a property of the store: claiming a pending record
transitions PENDING -> (APPROVED|REJECTED) atomically, and a second claim fails.

  * InMemoryPendingStore   — unit-testable model of the control.
  * DynamoDBPendingStore   — claim() is a conditional UpdateItem
                             (`#s = :pending`) so a double-approve is rejected by
                             DynamoDB itself; records carry a TTL so parked approvals
                             expire with the Step Functions task timeout.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class ClaimConflict(Exception):
    """Raised when a pending approval is claimed twice (already resolved) — single-use."""


class PendingApprovalStore:
    """Interface: put a pending approval, get it, list open ones, atomically claim it."""

    def put(self, record: Dict[str, Any]) -> str: raise NotImplementedError
    def get(self, approval_id: str) -> Optional[Dict[str, Any]]: raise NotImplementedError
    def list_pending(self) -> List[Dict[str, Any]]: raise NotImplementedError
    def claim(self, approval_id: str, new_status: str, by: str) -> Dict[str, Any]:
        """Transition PENDING -> new_status atomically; raise ClaimConflict otherwise."""
        raise NotImplementedError


class InMemoryPendingStore(PendingApprovalStore):
    def __init__(self) -> None:
        self._items: Dict[str, Dict[str, Any]] = {}

    def put(self, record: Dict[str, Any]) -> str:
        aid = record["approval_id"]
        record.setdefault("status", "PENDING")
        record.setdefault("created_at", int(time.time()))
        self._items[aid] = dict(record)
        return aid

    def get(self, approval_id: str) -> Optional[Dict[str, Any]]:
        r = self._items.get(approval_id)
        return dict(r) if r else None

    def list_pending(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self._items.values() if r.get("status") == "PENDING"]

    def claim(self, approval_id: str, new_status: str, by: str) -> Dict[str, Any]:
        r = self._items.get(approval_id)
        if not r:
            raise ClaimConflict(f"approval {approval_id} not found")
        if r.get("status") != "PENDING":
            raise ClaimConflict(f"approval {approval_id} already {r.get('status')}")
        r["status"] = new_status
        r["resolved_by"] = by
        r["resolved_at"] = int(time.time())
        return dict(r)


class DynamoDBPendingStore(PendingApprovalStore):  # pragma: no cover - requires boto3 + AWS
    """Conditional-update single-use claim; TTL-expiring pending records."""

    def __init__(self, table_name: str, client: Any = None, ttl_seconds: int = 3600) -> None:
        import boto3
        self._table = (client or boto3.resource("dynamodb")).Table(table_name)
        self._ttl = ttl_seconds

    def put(self, record: Dict[str, Any]) -> str:
        item = dict(record)
        item.setdefault("status", "PENDING")
        item.setdefault("created_at", int(time.time()))
        item.setdefault("ttl", int(time.time()) + self._ttl)
        self._table.put_item(Item=item)
        return item["approval_id"]

    def get(self, approval_id: str) -> Optional[Dict[str, Any]]:
        return self._table.get_item(Key={"approval_id": approval_id}).get("Item")

    def list_pending(self) -> List[Dict[str, Any]]:
        # status is a reserved word -> alias.
        resp = self._table.scan(
            FilterExpression="#s = :p",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":p": "PENDING"},
        )
        return resp.get("Items", [])

    def claim(self, approval_id: str, new_status: str, by: str) -> Dict[str, Any]:
        from botocore.exceptions import ClientError
        try:
            resp = self._table.update_item(
                Key={"approval_id": approval_id},
                UpdateExpression="SET #s = :new, resolved_by = :by, resolved_at = :t",
                ConditionExpression="#s = :pending",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":new": new_status, ":pending": "PENDING",
                                           ":by": by, ":t": int(time.time())},
                ReturnValues="ALL_NEW",
            )
            return resp["Attributes"]
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ClaimConflict(f"approval {approval_id} not PENDING (already resolved)") from exc
            raise
