# tools/gateway_tools.py
# ============================================================
# Gateway-backed tool access for the Resident Services & 311 agent.
#
# Every system-of-record call (311/CRM, knowledge base, identity, scheduling,
# GIS) goes through the MCP authorization gateway (reference logic for Bedrock
# AgentCore Gateway + Identity): the acting user's verified claims are authorized
# against a deny-by-default policy, high-risk writes (create a 311 request, book
# an appointment) require human approval, a short-lived scoped token is minted,
# and the attempt is audited (PII-masked).
# ============================================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "01-resident-services-311"

try:
    from slg_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def _invoke(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
            approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError(
            "MCP gateway unavailable; install platform_core. Production access to "
            "311/CRM, KB, identity, and scheduling must flow through the gateway."
        )
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool,
                           args=args, approval=approval)


def search_policy(claims: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    res = _invoke(claims, "kb.search_policy", {"query": query})
    return res.result if res.allowed else []


def get_service_request(claims: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    res = _invoke(claims, "crm311.get_service_request", {"request_id": request_id})
    return res.result if res.allowed else {}


def verify_resident(claims: Dict[str, Any], assertion: str) -> Dict[str, Any]:
    res = _invoke(claims, "identity.verify_resident", {"assertion": assertion})
    return res.result if res.allowed else {"verified": False}


def get_availability(claims: Dict[str, Any], service: str) -> Dict[str, Any]:
    res = _invoke(claims, "scheduling.get_availability", {"service": service})
    return res.result if res.allowed else {}


def create_service_request(claims: Dict[str, Any], payload: Dict[str, Any],
                           approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): open a 311 service request."""
    return _invoke(claims, "crm311.create_service_request", payload, approval=approval)


def book_appointment(claims: Dict[str, Any], payload: Dict[str, Any],
                     approval: Optional[Dict[str, Any]] = None) -> Any:
    """High-risk (write): book an appointment."""
    return _invoke(claims, "scheduling.book_appointment", payload, approval=approval)
