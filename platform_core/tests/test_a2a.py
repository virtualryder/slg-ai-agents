"""Tests for the A2A supervisor (holds no tool grants; forwards user claims)."""
from slg_agent_platform.a2a import Supervisor, INTENT_ROUTES, LIFE_EVENTS


def test_routes_intent_to_registered_agent():
    sup = Supervisor()
    seen = {}
    sup.register("01-resident-services-311", lambda claims, p: seen.update(claims) or {"ok": True})
    r = sup.route_intent("status_lookup", {"sub": "u1", "custom:slg_role": "RESIDENT_SERVICES_AGENT"}, {})
    assert r.handled and r.agent_id == "01-resident-services-311"
    assert seen["sub"] == "u1"  # original claims forwarded unchanged


def test_unrouted_intent_is_not_handled():
    assert not Supervisor().route_intent("teleport", {"sub": "u"}, {}).handled


def test_life_event_runs_ordered_intents():
    sup = Supervisor()
    calls = []
    for aid in set(INTENT_ROUTES.values()):
        sup.register(aid, lambda claims, p, aid=aid: calls.append(aid) or {"agent": aid})
    results = sup.run_life_event("moving", {"sub": "u"}, {})
    assert len(results) == len(LIFE_EVENTS["moving"])
    assert all(r.handled for r in results)
