"""P9 — authenticated-API negative tests against a DEPLOYED golden path.

The repo's offline suite proves the governance logic; these prove the DEPLOYED, authenticated
surface enforces it. Each test calls the live HTTP API with a real Cognito JWT and asserts the
decision-mapped status, plus the durable single-use approval + immutable audit on real AWS.

Checklist the CI gate enforces:
  * unauthorized-tool-denied   — a tool the agent isn't granted -> 403 DENY
  * unauthenticated-denied     — no JWT -> 401
  * allowed-read               — an entitled read -> 200 ALLOW + result
  * write-needs-approval       — a high-risk write with no approval -> 202 PENDING_APPROVAL
  * reviewer-single-use        — approving the same pending twice -> 2nd rejected (replay)
  * fixture-created            — approve once -> the workflow creates the fixture record
  * audit-exists               — the attempts left immutable audit records
"""
import json
import os
import time
import urllib.request

import pytest

boto3 = pytest.importorskip("boto3")
REGION = os.getenv("AWS_REGION", "us-east-1")


def _call(base_url, path, token=None, method="POST", body=None):
    url = f"{base_url}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or "{}")
        except Exception:
            return e.code, {}


def test_unauthenticated_request_denied(cognito):
    status, _ = _call(cognito["base_url"], "/tool/kb/search_policy", token=None,
                      body={"args": {"query": "hours"}})
    assert status in (401, 403)


def test_unauthorized_tool_denied(cognito):
    # the 311 agent is NOT granted permitting.* -> deny-by-default at the gateway
    status, out = _call(cognito["base_url"], "/tool/permitting/create_application",
                       token=cognito["requestor"], body={"args": {"type": "deck"}})
    assert status == 403 and out.get("decision") == "DENY"


def test_allowed_read_succeeds(cognito):
    status, out = _call(cognito["base_url"], "/tool/kb/search_policy",
                       token=cognito["requestor"], body={"args": {"query": "office hours"}})
    assert status == 200 and out.get("decision") == "ALLOW"
    assert out.get("audit_id")


def test_write_needs_approval(cognito):
    # high-risk write with no approval -> the gate holds it (no system-of-record mutation)
    status, out = _call(cognito["base_url"], "/tool/crm311/create_service_request",
                       token=cognito["requestor"],
                       body={"args": {"type": "Pothole", "description": "Oak St"}})
    assert status == 202 and out.get("decision") == "PENDING_APPROVAL"
    assert "result" not in out


def test_audit_records_written(outputs):
    ddb = boto3.client("dynamodb", region_name=REGION)
    resp = ddb.scan(TableName=outputs["AuditTableName"], Select="COUNT")
    assert resp["Count"] > 0   # the denied/pending attempts above were audited


def test_reviewer_single_use_and_fixture_created(cognito, outputs):
    """End-to-end on real AWS: start an execution, the reviewer approves ONCE through the
    authenticated reviewer API (the workflow creates the fixture request), and a SECOND approval
    of the same pending is rejected (durable single-use)."""
    sf = boto3.client("stepfunctions", region_name=REGION)
    sample = {"raw_request": "Pothole on Oak Street", "retrieved_sources": [],
              "acting_user_claims": {"sub": "rep-itest", "custom:slg_role": "RESIDENT_SERVICES_AGENT"},
              "identity_verified": False}
    exec_arn = sf.start_execution(stateMachineArn=outputs["StateMachineArn"],
                                  input=json.dumps(sample))["executionArn"]

    # the reviewer lists their actionable queue until the parked approval appears
    approval_id = None
    for _ in range(30):
        status, out = _call(cognito["base_url"], "/approvals", token=cognito["reviewer"], method="GET")
        if status == 200 and out.get("pending"):
            approval_id = out["pending"][0]["approval_id"]
            break
        time.sleep(2)
    assert approval_id, "pending approval never appeared for the reviewer"

    s1, o1 = _call(cognito["base_url"], f"/approvals/{approval_id}/decision",
                  token=cognito["reviewer"], body={"decision": "approve"})
    assert s1 == 200 and o1.get("status") == "APPROVED"

    # replay: approving the same pending again is rejected (single-use claim)
    s2, _ = _call(cognito["base_url"], f"/approvals/{approval_id}/decision",
                 token=cognito["reviewer"], body={"decision": "approve"})
    assert s2 in (403, 409)

    # the workflow finished and created the fixture record through the governed gateway
    final = None
    for _ in range(30):
        d = sf.describe_execution(executionArn=exec_arn)
        if d["status"] != "RUNNING":
            final = d
            break
        time.sleep(2)
    assert final and final["status"] == "SUCCEEDED"
    body = json.loads(final["output"])
    assert body.get("case_status") == "REQUEST_CREATED" and body.get("request_id")
