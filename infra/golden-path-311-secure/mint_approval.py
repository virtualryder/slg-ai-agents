#!/usr/bin/env python3
"""Reviewer STAND-IN for the 311 smoke test (P7 replaces this with a real reviewer service).

Mints a BOUND, single-use, separation-of-duties approval token for the exact pending write
(crm311.create_service_request with the same args finalize computes) and prints the
SendTaskSuccess task-output JSON: {"token": <bound>, "reviewer": {...}}.

Requires APPROVAL_TOKEN_SECRET to equal the stack's TokenSecret so the token verifies inside
the finalize Lambda. This is a dev convenience; production uses an authenticated reviewer
service that holds the key in Secrets Manager / KMS and enforces reviewer entitlement.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
from slg_agent_platform.mcp_gateway import approvals  # noqa: E402

_SAMPLE = os.path.join(_HERE, "..", "..", "aws-native-reference", "01-resident-services-311", "sample_input.json")
raw = json.load(open(_SAMPLE))
args = {"type": "General", "description": raw.get("raw_request", "")}
requestor = (raw.get("acting_user_claims") or {}).get("sub", "rep-1")
approver = os.getenv("REVIEWER_SUB", "cs-supervisor-1")  # MUST differ from requestor (SoD)

token = approvals.mint_approval_token(
    requestor=requestor, agent_id="01-resident-services-311",
    tool="crm311.create_service_request", args=args, approver=approver,
)
print(json.dumps({"token": token, "reviewer": {"sub": approver, "role": "RESIDENT_SERVICES_SUPERVISOR"}}))
