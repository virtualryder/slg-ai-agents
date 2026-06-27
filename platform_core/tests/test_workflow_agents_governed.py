"""Agents 02-08: each workflow's consequential write runs THROUGH the governed gateway.

Loads each agent's REAL finalize.py and proves the write executes only with a bound,
SoD approval (ALLOW -> ACTION_COMPLETED + result + audit) and is BLOCKED otherwise.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from slg_agent_platform.mcp_gateway import approvals

_AWS = Path(__file__).resolve().parents[2] / "aws-native-reference"

# agent -> (write action, acting role, expected tool)
CASES = {
    "02-forms-idp": ("ASSEMBLE", "INTAKE_SPECIALIST", "idp.assemble_form"),
    "03-permitting-licensing": ("CREATE_APPLICATION", "PERMIT_TECH", "permitting.create_application"),
    "04-benefits-caseworker": ("CREATE_APPLICATION", "ELIGIBILITY_CASEWORKER", "eligibility.create_application"),
    "05-public-records-foia": ("ASSEMBLE_PACKAGE", "RECORDS_TECH", "records.assemble_package"),
    "06-procurement-grants": ("DRAFT_RFP", "PROCUREMENT_ANALYST", "procurement.draft_rfp"),
    "07-govops-service-desk": ("CREATE_TICKET", "IT_ANALYST", "itsm.create_ticket"),
    "08-public-safety-health": ("DRAFT_REPORT", "PUBLIC_SAFETY_ANALYST", "safety.draft_report"),
}


def _load_finalize(aid):
    lam = _AWS / aid / "lambdas"
    for m in ("_shared", "core", "finalize"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(lam))
    spec = importlib.util.spec_from_file_location(f"finalize_{aid.replace('-', '_')}", lam / "finalize.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _event(action, role, raw="P5 propagation test"):
    return {"recommended_action": action, "requires_human_write": True,
            "acting_user_claims": {"sub": "staff-1", "custom:slg_role": role},
            "raw_request": raw}


@pytest.mark.parametrize("aid", list(CASES))
def test_write_executes_through_gateway_with_bound_approval(aid):
    action, role, tool = CASES[aid]
    finalize = _load_finalize(aid)
    e = _event(action, role)
    args = {"type": "General", "description": e["raw_request"]}
    token = approvals.mint_approval_token(requestor="staff-1", agent_id=aid, tool=tool,
                                          args=args, approver="supervisor-1")
    e["approval"] = {"token": token, "reviewer": {"sub": "supervisor-1"}}
    out = finalize.handler(e)["body"]
    assert out["case_status"] == "ACTION_COMPLETED", (aid, out)
    assert out["gateway_decision"] == "ALLOW" and out["tool"] == tool
    assert out["result"] and out["audit_id"]


@pytest.mark.parametrize("aid", list(CASES))
def test_write_blocked_without_approval(aid):
    action, role, _ = CASES[aid]
    finalize = _load_finalize(aid)
    out = finalize.handler(_event(action, role))["body"]
    assert out["case_status"] == "BLOCKED_NO_APPROVAL", (aid, out)
    assert "result" not in out
