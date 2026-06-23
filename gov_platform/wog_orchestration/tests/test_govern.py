from gov_platform.wog_orchestration.govern import default_catalog, GovernedToolGateway, GovernedTool, ToolCatalog

CASEWORKER = {"sub": "cw-1", "custom:slg_role": "ELIGIBILITY_CASEWORKER"}
INTAKE = {"sub": "i-1", "custom:slg_role": "INTAKE_SPECIALIST"}

def gw():
    return GovernedToolGateway(default_catalog())

def test_purpose_binding_denies_wrong_purpose():
    g = gw()
    r = g.invoke(user_claims=CASEWORKER, agent_id="04-benefits-caseworker",
                 tool="eligibility.create_application", purpose="fraud_sweep",
                 args={"program": "SNAP"}, approval={"approved": True, "reviewer": {"sub": "sup"}})
    assert r.decision == "DENY" and "purpose" in r.reason

def test_allowed_purpose_delegates_to_gateway_with_approval():
    g = gw()
    r = g.invoke(user_claims=CASEWORKER, agent_id="04-benefits-caseworker",
                 tool="eligibility.create_application", purpose="benefits",
                 args={"program": "SNAP"}, approval={"approved": True, "reviewer": {"sub": "sup"}})
    assert r.allowed and r.decision == "ALLOW"
    assert r.governance["agency"] == "HHS" and "PHI" in r.governance["data_classes"]

def test_residency_mismatch_denied():
    cat = ToolCatalog()
    cat.register(GovernedTool("eligibility.create_application", "HHS", frozenset({"benefits"}),
                              data_classes=("PII",), residency="us-gov"))
    g = GovernedToolGateway(cat, deployment_residency="us")
    r = g.invoke(user_claims=CASEWORKER, agent_id="04-benefits-caseworker",
                 tool="eligibility.create_application", purpose="benefits", args={})
    assert r.decision == "DENY" and "residency" in r.reason

def test_transaction_threshold_denied():
    cat = ToolCatalog()
    cat.register(GovernedTool("eligibility.create_application", "HHS", frozenset({"benefits"}),
                              data_classes=("PII",), max_amount=1000))
    g = GovernedToolGateway(cat)
    r = g.invoke(user_claims=CASEWORKER, agent_id="04-benefits-caseworker",
                 tool="eligibility.create_application", purpose="benefits", args={}, amount=5000)
    assert r.decision == "DENY" and "threshold" in r.reason

def test_idempotent_replay_suppressed():
    g = gw()
    kw = dict(user_claims=INTAKE, agent_id="02-forms-idp", tool="idp.assemble_form",
              purpose="moving", args={"form_id": "MV-1"}, approval={"approved": True, "reviewer": {"sub": "s"}},
              idempotency_key="idem-1")
    a = g.invoke(**kw); b = g.invoke(**kw)
    assert a.allowed and b.decision == "DEDUP"

def test_successful_write_registers_rollback():
    g = gw()
    g.invoke(user_claims=INTAKE, agent_id="02-forms-idp", tool="crm311.create_service_request",
             purpose="moving", args={"type": "Address Change"},
             approval={"approved": True, "reviewer": {"sub": "s"}})
    assert any(rb["tool"] == "crm311.create_service_request" for rb in g.rollbacks)
