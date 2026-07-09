#!/usr/bin/env python3
"""
SLG Agent 01 (Resident Services / 311) — NEGATIVE DEMO (the 10 things the platform refuses).

Exercises the SHIPPING controls (slg_agent_platform.*) and proves each refusal fires. Nothing is
mocked except two deliberate fault injections (masker down, audit sink down) proving fail-closed.

Run:  PYTHONPATH=platform_core:. python 01-resident-services-311/demo/negative_demo.py
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from slg_agent_platform import budget, jwt_verify
from slg_agent_platform.mcp_gateway import approvals
from slg_agent_platform.mcp_gateway import audit as audit_mod
from slg_agent_platform.mcp_gateway.gateway import MCPGateway
from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog

AGENT = "01-resident-services-311"
USER = {"sub": "u-agent", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}
WRONG = {"sub": "u-it", "custom:slg_role": "IT_ANALYST"}          # not entitled to crm311.*
READ = "crm311.get_service_request"
WRITE = "crm311.create_service_request"                            # high-risk (needs approval)
ARGS = {"request_id": "SR-1"}

results = []


def rec(n, name, ok, detail):
    results.append((n, name, ok, detail))


def gw():
    return MCPGateway(audit=GatewayAuditLog(), connector_mode="fixture")


def run():
    # 1 — no JWT
    r = gw().invoke(user_claims={}, agent_id=AGENT, tool=READ, args=ARGS)
    rec(1, "no JWT / unauthenticated", r.decision == "DENY", r.reason)

    # 2 — bad JWT (alg 'none' / malformed -> rejected)
    try:
        jwt_verify.verify_jwt("eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.", jwks={"keys": []},
                              issuer="https://issuer", audience="app")
        rec(2, "bad / unverifiable JWT", False, "accepted (BUG)")
    except jwt_verify.JWTInvalid as e:
        rec(2, "bad / unverifiable JWT", True, str(e))

    # 3 — wrong role (human not entitled)
    r = gw().invoke(user_claims=WRONG, agent_id=AGENT, tool=READ, args=ARGS)
    rec(3, "wrong role (not entitled)", r.decision == "DENY", r.reason)

    # 4 — unregistered tool
    r = gw().invoke(user_claims=USER, agent_id=AGENT, tool="crm311.exfiltrate_all", args={})
    rec(4, "unregistered tool", r.decision == "DENY", r.reason)

    # 5 — self-approval (SoD refused at mint)
    try:
        approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-a")
        rec(5, "self-approval", False, "minted (BUG)")
    except approvals.ApprovalInvalid as e:
        rec(5, "self-approval", True, str(e))

    # 6 — approval replay (single-use via nonce store)
    nonces = approvals.NonceStore()
    tok = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=nonces)
    try:
        approvals.verify_approval_token(tok, requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, nonce_store=nonces)
        rec(6, "approval replay", False, "second use accepted (BUG)")
    except approvals.ApprovalInvalid as e:
        rec(6, "approval replay", True, str(e))

    # 7 — tampered args
    tok2 = approvals.mint_approval_token(requestor="u-a", agent_id=AGENT, tool=WRITE, args=ARGS, approver="u-sup")
    try:
        approvals.verify_approval_token(tok2, requestor="u-a", agent_id=AGENT, tool=WRITE, args={"request_id": "SR-999"})
        rec(7, "tampered args", False, "accepted (BUG)")
    except approvals.ApprovalInvalid as e:
        rec(7, "tampered args", True, str(e))

    # 8 — masking failure -> fail-closed
    log = GatewayAuditLog()
    orig = audit_mod.mask
    audit_mod.mask = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("masker unavailable"))
    try:
        log.record({"decision": "ALLOW", "tool": READ, "args": {"note": "resident SSN 123-45-6789"}})
        rec(8, "masking failure (fail-closed)", False, "written unmasked (BUG)")
    except Exception as e:
        rec(8, "masking failure (fail-closed)", len(log.records) == 0,
            f"raised {type(e).__name__}; no record persisted={len(log.records) == 0}")
    finally:
        audit_mod.mask = orig

    # 9 — audit-sink failure -> fail-closed
    g = gw()
    g.audit.record = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("audit sink down"))
    try:
        g.invoke(user_claims=USER, agent_id=AGENT, tool=READ, args=ARGS)
        rec(9, "audit-write failure (fail-closed)", False, "success with no audit (BUG)")
    except Exception as e:
        rec(9, "audit-write failure (fail-closed)", True, f"raised {type(e).__name__}")

    # 10 — budget exceeded before spend
    m = budget.BudgetMeter(agent_id=AGENT, dept="311", monthly_token_cap=1000, cap_behavior="hard")
    m.commit(900)
    d = m.preflight(500)
    rec(10, "budget exceeded (pre-spend)", d.allowed is False, d.reason)


def main():
    print("=" * 70)
    print("  SLG AGENT 01 (311) — NEGATIVE DEMO (what the platform REFUSES)")
    print("=" * 70)
    run()
    ok = 0
    for n, name, denied, detail in results:
        tag = "DENIED ✓" if denied else "LEAKED ✗"
        ok += 1 if denied else 0
        print(f"  {n:>2}. [{tag}] {name:<34} {str(detail)[:66]}")
    print("-" * 70)
    allpass = ok == len(results)
    print(f"  {ok}/{len(results)} refusals fired. "
          + ("ALL DENIES ENFORCED ✓" if allpass else "SOME CONTROL FAILED ✗"))
    print("=" * 70)
    return 0 if allpass else 1


if __name__ == "__main__":
    sys.exit(main())
