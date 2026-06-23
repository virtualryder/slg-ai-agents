"""AWS-backed stores tested with fake boto3 clients — no AWS account needed."""
import sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "lambdas")]
from aws_backends import AwsConsentStore, AwsComplianceEventBus
from gov_platform.wog_orchestration.events.bus import ComplianceEvent


class FakeDDB:
    def __init__(self): self.items = {}
    def put_item(self, TableName, Item):
        # key by the hash+range present in the item
        if "scope" in Item:
            k = (Item["resident_ref"]["S"], Item["scope"]["S"])
        else:
            k = (Item["correlation_id"]["S"], Item["ts"]["S"])
        self.items[k] = Item
        return {}
    def get_item(self, TableName, Key):
        k = (Key["resident_ref"]["S"], Key["scope"]["S"])
        return {"Item": self.items[k]} if k in self.items else {}


class FakeEvents:
    def __init__(self): self.sent = []
    def put_events(self, Entries): self.sent.extend(Entries); return {"FailedEntryCount": 0}


def test_consent_store_record_then_check():
    ddb = FakeDDB()
    store = AwsConsentStore("consent", client=ddb)
    assert not store.check("RES-1", "moving:form").allowed       # nothing yet
    store.record("RES-1", "moving:form", "AAL2")
    d = store.check("RES-1", "moving:form", required_aal="AAL2")
    assert d.allowed and d.consent_id

def test_consent_store_insufficient_aal():
    ddb = FakeDDB(); store = AwsConsentStore("consent", client=ddb)
    store.record("RES-1", "moving:form", "AAL1")
    assert not store.check("RES-1", "moving:form", required_aal="AAL2").allowed

def test_event_bus_persists_and_routes():
    ddb = FakeDDB(); ev = FakeEvents()
    bus = AwsComplianceEventBus("events", "slg-wog-bus", ddb_client=ddb, events_client=ev)
    bus.publish(ComplianceEvent("moving.form.committed", "RES-1", "SS", "form",
                                data_classes=["PII", "FTI"], correlation_id="C1", detail="x"))
    assert len(bus.log) == 1                 # in-memory log still works (evidence assembly)
    assert len(ddb.items) == 1               # persisted to DynamoDB
    assert len(ev.sent) == 1                 # routed to EventBridge
    assert ev.sent[0]["EventBusName"] == "slg-wog-bus"

def test_bootstrap_memory_mode(monkeypatch):
    monkeypatch.setenv("WOG_BACKEND", "memory")
    import _shared
    _shared.GOVGW = None
    _shared.bootstrap()
    assert _shared.GOVGW is not None and _shared.CONSENT is not None


class FakeIdemDDB:
    def __init__(self): self.keys = set()
    def put_item(self, TableName, Item, ConditionExpression=None):
        k = Item["idempotency_key"]["S"]
        if k in self.keys:
            raise type("ConditionalCheckFailedException", (Exception,), {})()
        self.keys.add(k); return {}

def test_idempotency_store_claims_once():
    from aws_backends import AwsIdempotencyStore
    st = AwsIdempotencyStore("idem", client=FakeIdemDDB())
    assert st.seen("k1") is False     # first time claims it
    assert st.seen("k1") is True      # second time already seen
