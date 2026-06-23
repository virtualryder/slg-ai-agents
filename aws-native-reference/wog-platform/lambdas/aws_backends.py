"""
AWS-backed implementations of the WoG stateful stores — same interfaces as the
in-memory ConsentLedger / ComplianceEventBus, so the Lambda handlers and the
saga coordinator are unchanged. Selected at runtime by WOG_BACKEND=aws.

  AwsConsentStore        -> DynamoDB consent table  (resident_ref, scope)
  AwsComplianceEventBus  -> DynamoDB event store (correlation_id, ts) + EventBridge

boto3 is imported lazily and clients may be injected (used by the tests with
fakes) so this module imports and unit-tests with no AWS account.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from gov_platform.wog_orchestration.consent.service import ConsentDecision
from gov_platform.wog_orchestration.events.bus import ComplianceEventBus, ComplianceEvent
from slg_agent_platform.pii import mask

_AAL_ORDER = {"NONE": 0, "AAL1": 1, "AAL2": 2, "AAL3": 3}


def _client(service: str, injected: Optional[Any], region: Optional[str]) -> Any:
    if injected is not None:
        return injected
    import boto3  # lazy — only needed in AWS
    return boto3.client(service, region_name=region or os.getenv("AWS_REGION", "us-east-1"))


class AwsConsentStore:
    """Consent ledger backed by a DynamoDB table keyed (resident_ref, scope)."""

    def __init__(self, table: str, region: Optional[str] = None, client: Optional[Any] = None) -> None:
        self.table = table
        self._ddb = _client("dynamodb", client, region)

    def record(self, resident_ref: str, scope: str, assurance_level: str, ttl_days: int = 365) -> str:
        cid = f"CNS-{uuid.uuid4().hex[:8]}"
        expires = (_dt.date.today() + _dt.timedelta(days=ttl_days)).isoformat()
        self._ddb.put_item(TableName=self.table, Item={
            "resident_ref": {"S": resident_ref}, "scope": {"S": scope},
            "consent_id": {"S": cid}, "assurance_level": {"S": assurance_level},
            "expires": {"S": expires},
            "granted_at": {"S": _dt.datetime.now(_dt.timezone.utc).isoformat()},
        })
        return cid

    def check(self, resident_ref: str, scope: str, required_aal: str = "AAL2") -> ConsentDecision:
        resp = self._ddb.get_item(TableName=self.table,
                                  Key={"resident_ref": {"S": resident_ref}, "scope": {"S": scope}})
        item = resp.get("Item")
        if not item:
            return ConsentDecision(False, f"no consent on file for scope {scope!r}")
        have = _AAL_ORDER.get(item["assurance_level"]["S"], 0)
        if have < _AAL_ORDER.get(required_aal, 99):
            return ConsentDecision(False,
                f"assurance {item['assurance_level']['S']} < required {required_aal}",
                item["consent_id"]["S"])
        if item["expires"]["S"] < _dt.date.today().isoformat():
            return ConsentDecision(False, "consent expired", item["consent_id"]["S"])
        return ConsentDecision(True, "valid consent", item["consent_id"]["S"])


class AwsComplianceEventBus(ComplianceEventBus):
    """Event bus that ALSO persists each event to DynamoDB and puts it on EventBridge."""

    def __init__(self, event_table: str, bus_name: str, region: Optional[str] = None,
                 ddb_client: Optional[Any] = None, events_client: Optional[Any] = None) -> None:
        super().__init__()
        self.event_table = event_table
        self.bus_name = bus_name
        self._ddb = _client("dynamodb", ddb_client, region)
        self._events = _client("events", events_client, region)

    def publish(self, ev: ComplianceEvent) -> str:
        eid = super().publish(ev)            # appends masked record to self._log
        rec = self._log[-1]
        # 1. durable append-only store (case-level partition = correlation_id)
        self._ddb.put_item(TableName=self.event_table, Item={
            "correlation_id": {"S": rec.get("correlation_id") or rec["resident_ref"]},
            "ts": {"S": rec["ts"]}, "event_id": {"S": rec["event_id"]},
            "event_type": {"S": rec["event_type"]}, "agency": {"S": rec["agency"]},
            "data_classes": {"S": json.dumps(rec.get("data_classes", []))},
            "detail": {"S": mask(rec.get("detail", ""))},
        })
        # 2. route to subscribers via EventBridge
        self._events.put_events(Entries=[{
            "Source": "slg.wog", "DetailType": rec["event_type"], "EventBusName": self.bus_name,
            "Detail": json.dumps(rec),
        }])
        return eid


class AwsIdempotencyStore:
    """Exactly-once across Lambda invocations via a DynamoDB conditional put."""

    def __init__(self, table: str, region: Optional[str] = None, client: Optional[Any] = None,
                 ttl_days: int = 7) -> None:
        self.table = table
        self.ttl_days = ttl_days
        self._ddb = _client("dynamodb", client, region)

    def seen(self, key: str) -> bool:
        """Return True if this key was already processed; otherwise claim it (False)."""
        ttl = int((_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=self.ttl_days)).timestamp())
        try:
            self._ddb.put_item(
                TableName=self.table,
                Item={"idempotency_key": {"S": key}, "ttl": {"N": str(ttl)}},
                ConditionExpression="attribute_not_exists(idempotency_key)",
            )
            return False
        except Exception as exc:  # ConditionalCheckFailedException -> already processed
            if exc.__class__.__name__ == "ConditionalCheckFailedException" or "ConditionalCheck" in str(exc):
                return True
            raise
