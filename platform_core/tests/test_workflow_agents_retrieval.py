"""Agents 02-08: the governed RAG retrieve/draft/check chain runs offline-green.

Loads each agent's REAL retrieve.py -> draft.py -> check.py (the same modules the deployed
Step Functions states invoke) and proves: retrieval grounds via the governed gateway
(kb.search_policy ALLOW for an entitled role -> sources + audit id), the draft is built
from those sources with a deterministic fallback (no Bedrock creds in CI), and check emits
a recommended action + write flag. Deny path: an unentitled role keeps fallback sources.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_AWS = Path(__file__).resolve().parents[2] / "aws-native-reference"

# agent -> (entitled acting role)
ROLES = {
    "02-forms-idp": "INTAKE_SPECIALIST",
    "03-permitting-licensing": "PERMIT_TECH",
    "04-benefits-caseworker": "ELIGIBILITY_CASEWORKER",
    "05-public-records-foia": "RECORDS_TECH",
    "06-procurement-grants": "PROCUREMENT_ANALYST",
    "07-govops-service-desk": "IT_ANALYST",
    "08-public-safety-health": "PUBLIC_SAFETY_ANALYST",
}


def _load(aid, name):
    lam = _AWS / aid / "lambdas"
    for m in ("_shared", "core", name):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(lam))
    sys.path.insert(0, str(_AWS / aid))
    spec = importlib.util.spec_from_file_location(f"{name}_{aid.replace('-', '_')}", lam / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _event(role):
    return {"raw_request": "How do I file this with the city?",
            "acting_user_claims": {"sub": "staff-1", "custom:slg_role": role}}


@pytest.mark.parametrize("aid", list(ROLES))
def test_retrieve_draft_check_chain_grounds_through_gateway(aid):
    retrieve = _load(aid, "retrieve")
    draft = _load(aid, "draft")
    check = _load(aid, "check")
    e = retrieve.handler(_event(ROLES[aid]))["body"]
    assert e["retrieval_decision"] == "ALLOW"          # governed kb.search_policy read allowed
    assert e["retrieved_sources"] and e["retrieval_audit_id"]   # audited read
    e = draft.handler(e)["body"]
    assert e["draft_answer"] and e["draft_via"] == "deterministic"   # offline fallback
    e = check.handler(e)["body"]
    assert "recommended_action" in e and "grounded" in e


@pytest.mark.parametrize("aid", list(ROLES))
def test_retrieval_denied_for_unentitled_role_keeps_fallback(aid):
    retrieve = _load(aid, "retrieve")
    e = dict(_event("UNRELATED_ROLE"))
    e["retrieved_sources"] = [{"title": "fallback", "snippet": "kept", "url": "https://x.gov"}]
    out = retrieve.handler(e)["body"]
    assert out["retrieval_decision"] == "DENY"          # gateway denied the read
    assert out["retrieved_sources"][0]["title"] == "fallback"   # fail-safe kept event sources
