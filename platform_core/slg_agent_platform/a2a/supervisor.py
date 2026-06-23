"""
A2A supervisor — governed agent-to-agent routing for cross-agency workflows.

A whole-of-government "life event" (move, new child, start a business, lose a
job, disaster, bereavement) spans several specialist agents. The supervisor
routes the resident's intent to the right specialist, FORWARDS THE ORIGINAL USER
CLAIMS unchanged, and aggregates results. Critically, the supervisor holds NO
tool grants of its own: it can invoke specialists, never systems of record
directly. Every consequential system touch still happens through a specialist
→ MCP gateway → connector path, with that specialist's grant ∩ the user's
entitlement enforced. This mirrors AgentCore's A2A/agent-as-tool model.

ADR: in-process routing today; AgentCore Runtime + A2A when specialists are
deployed as independent services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Intent -> specialist agent id. Extended as agents are added.
INTENT_ROUTES: Dict[str, str] = {
    "service_request": "01-resident-services-311",
    "status_lookup": "01-resident-services-311",
    "appointment": "01-resident-services-311",
    "form": "02-forms-idp",
    "application": "02-forms-idp",
    "permit": "03-permitting-licensing",
    "license": "03-permitting-licensing",
    "benefits": "04-benefits-caseworker",
    "records_request": "05-public-records-foia",
    "foia": "05-public-records-foia",
    "procurement": "06-procurement-grants",
    "grant": "06-procurement-grants",
    "it_support": "07-govops-service-desk",
    "incident_report": "08-public-safety-health",
}

# Life event -> ordered list of intents the supervisor coordinates.
LIFE_EVENTS: Dict[str, List[str]] = {
    "moving": ["service_request", "form", "appointment"],
    "new_business": ["permit", "form", "procurement"],
    "job_loss": ["benefits", "form"],
    "disaster": ["service_request", "benefits", "incident_report"],
}


@dataclass
class RouteResult:
    intent: str
    agent_id: Optional[str]
    handled: bool
    output: Any = None
    reason: str = ""


@dataclass
class Supervisor:
    """Routes intents/life-events to specialist agents; holds no tool grants."""
    registry: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Any]] = field(default_factory=dict)

    def register(self, agent_id: str, handler: Callable[[Dict[str, Any], Dict[str, Any]], Any]) -> None:
        self.registry[agent_id] = handler

    def route_intent(self, intent: str, user_claims: Dict[str, Any], payload: Dict[str, Any]) -> RouteResult:
        agent_id = INTENT_ROUTES.get(intent)
        if not agent_id:
            return RouteResult(intent, None, False, reason=f"no route for intent {intent!r}")
        handler = self.registry.get(agent_id)
        if not handler:
            return RouteResult(intent, agent_id, False, reason=f"agent {agent_id!r} not registered")
        # forward the ORIGINAL user claims — the supervisor never elevates them
        out = handler(user_claims, payload)
        return RouteResult(intent, agent_id, True, output=out)

    def run_life_event(self, event: str, user_claims: Dict[str, Any],
                       payload: Dict[str, Any]) -> List[RouteResult]:
        intents = LIFE_EVENTS.get(event, [])
        results: List[RouteResult] = []
        for intent in intents:
            results.append(self.route_intent(intent, user_claims, payload))
        return results
