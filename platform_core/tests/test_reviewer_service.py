"""P7 reviewer service: the authenticated human-approval decision.

Proves the real service enforces what the mint_approval.py stand-in could not:
authority (reviewer entitled to the tool), separation of duties, single-use, server-side
token minting, Step Functions resume, and an append-only audit of every decision — and that
the minted token actually verifies against the bound request (i.e. finalize would accept it).
"""
import pytest

from slg_agent_platform.mcp_gateway import approvals
from slg_agent_platform.reviewer import ReviewerService, ReviewerError, InMemoryPendingStore


AGENT = "03-permitting-licensing"
TOOL = "permitting.create_application"
ARGS = {"type": "General", "description": "new deck permit"}


class FakeSfn:
    def __init__(self): self.success = []; self.failure = []
    def send_task_success(self, task_token, output): self.success.append((task_token, output))
    def send_task_failure(self, task_token, error, cause): self.failure.append((task_token, error, cause))


def _pending(store, requestor="permit-tech-1", approval_id="ap-1"):
    store.put({"approval_id": approval_id, "task_token": "tok-123", "agent_id": AGENT,
               "requestor": requestor, "tool": TOOL, "args": ARGS})
    return approval_id


def _svc():
    store = InMemoryPendingStore()
    sfn = FakeSfn()
    return ReviewerService(store, sfn=sfn), store, sfn


def _claims(sub, role): return {"sub": sub, "custom:slg_role": role}


def test_approve_mints_bound_token_resumes_and_audits():
    svc, store, sfn = _svc()
    aid = _pending(store)
    out = svc.decide(_claims("permit-official-1", "PERMIT_OFFICIAL"), aid, "approve")
    assert out["status"] == "APPROVED" and out["token"] and out["audit_id"]
    # the execution was resumed exactly once with the token
    assert len(sfn.success) == 1 and sfn.success[0][0] == "tok-123"
    assert sfn.success[0][1]["token"] == out["token"]
    # the minted token VERIFIES against the exact bound request (finalize would accept it)
    claims = approvals.verify_approval_token(
        out["token"], requestor="permit-tech-1", agent_id=AGENT, tool=TOOL, args=ARGS)
    assert claims["approver"] == "permit-official-1"
    # decision is on the append-only audit
    assert any(r["decision"] == "APPROVAL_GRANTED" for r in svc._audit.records)


def test_self_approval_blocked_by_separation_of_duties():
    svc, store, sfn = _svc()
    aid = _pending(store, requestor="permit-tech-1")
    with pytest.raises(ReviewerError):
        svc.decide(_claims("permit-tech-1", "PERMIT_OFFICIAL"), aid, "approve")
    assert sfn.success == []                       # nothing resumed
    assert store.get(aid)["status"] == "PENDING"   # not consumed — a real reviewer can still act
    assert any(r["decision"] == "APPROVAL_DENIED" for r in svc._audit.records)


def test_reviewer_without_authority_cannot_approve():
    svc, store, sfn = _svc()
    aid = _pending(store)
    # IT_ANALYST is not entitled to permitting.create_application
    with pytest.raises(ReviewerError):
        svc.decide(_claims("it-1", "IT_ANALYST"), aid, "approve")
    assert sfn.success == []
    assert store.get(aid)["status"] == "PENDING"


def test_single_use_second_approval_rejected():
    svc, store, sfn = _svc()
    aid = _pending(store)
    svc.decide(_claims("permit-official-1", "PERMIT_OFFICIAL"), aid, "approve")
    with pytest.raises(ReviewerError):                # already resolved
        svc.decide(_claims("permit-official-2", "PERMIT_OFFICIAL"), aid, "approve")
    assert len(sfn.success) == 1                       # not resumed twice


def test_reject_fails_the_task_and_audits():
    svc, store, sfn = _svc()
    aid = _pending(store)
    out = svc.decide(_claims("permit-official-1", "PERMIT_OFFICIAL"), aid, "reject", comment="incomplete")
    assert out["status"] == "REJECTED"
    assert len(sfn.failure) == 1 and sfn.failure[0][1] == "REJECTED_BY_REVIEWER"
    assert sfn.success == []
    assert any(r["decision"] == "APPROVAL_REJECTED" for r in svc._audit.records)


def test_list_pending_filters_to_actionable_for_this_reviewer():
    svc, store, _ = _svc()
    _pending(store, requestor="permit-tech-1", approval_id="ap-1")
    _pending(store, requestor="permit-official-1", approval_id="ap-2")  # reviewer is requestor here
    visible = svc.list_pending(_claims("permit-official-1", "PERMIT_OFFICIAL"))
    ids = {v["approval_id"] for v in visible}
    assert "ap-1" in ids and "ap-2" not in ids       # SoD pre-filter hides own request
    # an unentitled reviewer sees none
    assert svc.list_pending(_claims("it-1", "IT_ANALYST")) == []


def test_reviewer_approval_token_is_accepted_by_the_agent_finalize():
    """End-to-end: reviewer approves -> server-minted bound token -> the REAL 03 finalize
    executes the write THROUGH the gateway (ACTION_COMPLETED). Proves the P7 service closes
    the loop with the deployed governed-write path, not just an isolated token check."""
    import importlib.util
    import sys
    from pathlib import Path

    aws = Path(__file__).resolve().parents[2] / "aws-native-reference" / "03-permitting-licensing"
    lam = aws / "lambdas"
    for m in ("_shared", "core", "finalize"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(lam))
    spec = importlib.util.spec_from_file_location("finalize_p7_03", lam / "finalize.py")
    finalize = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(finalize)

    svc, store, _ = _svc()
    store.put({"approval_id": "ap-9", "task_token": "tok-9", "agent_id": AGENT,
               "requestor": "permit-tech-1", "tool": TOOL, "args": ARGS})
    out = svc.decide(_claims("permit-official-1", "PERMIT_OFFICIAL"), "ap-9", "approve")

    # finalize computes args from the case; reviewer minted against the same args -> verifies
    event = {"recommended_action": "CREATE_APPLICATION", "requires_human_write": True,
             "request_type": "General", "raw_request": "new deck permit",
             "acting_user_claims": {"sub": "permit-tech-1", "custom:slg_role": "PERMIT_TECH"},
             "approval": {"token": out["token"], "reviewer": {"sub": "permit-official-1"}}}
    res = finalize.handler(event)["body"]
    assert res["case_status"] == "ACTION_COMPLETED" and res["gateway_decision"] == "ALLOW"
    assert res["tool"] == TOOL and res["audit_id"]
