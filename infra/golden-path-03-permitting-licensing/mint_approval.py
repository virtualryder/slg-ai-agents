#!/usr/bin/env python3
"""Reviewer STAND-IN for the 03-permitting-licensing smoke test (P7 replaces with a real reviewer service).
Computes the pending tool from the sample input and mints a BOUND, SoD approval token."""
import json, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
AGENT = "03-permitting-licensing"
sys.path.insert(0, os.path.join(_HERE, "..", "..", "platform_core"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT))
from slg_agent_platform.mcp_gateway import approvals  # noqa: E402
import core  # noqa: E402

ACTION_TOOL = {'CREATE_APPLICATION': 'permitting.create_application', 'ROUTE_REVIEW': 'permitting.route_review'}
raw = json.load(open(os.path.join(_HERE, "..", "..", "aws-native-reference", AGENT, "sample_input.json")))
action = core.recommended_action(core.classify(raw.get("raw_request", "")))
tool = ACTION_TOOL.get(action)
args = {"type": "General", "description": raw.get("raw_request", "")}
requestor = (raw.get("acting_user_claims") or {}).get("sub", "staff-1")
approver = os.getenv("REVIEWER_SUB", "licensed-plan-reviewer-1")
if tool:
    token = approvals.mint_approval_token(requestor=requestor, agent_id=AGENT, tool=tool, args=args, approver=approver)
    print(json.dumps({"token": token, "reviewer": {"sub": approver}}))
else:
    print(json.dumps({"approved": True, "reviewer": {"sub": approver}}))  # read action; finalize ignores
