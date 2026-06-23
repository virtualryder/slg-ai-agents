# tools/gateway_tools.py — Permitting & Licensing
# Every system-of-record call flows through the deny-by-default MCP gateway
# (reference logic for Bedrock AgentCore Gateway + Identity).
from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO / "platform_core"))

AGENT_ID = "03-permitting-licensing"
try:
    from slg_agent_platform.mcp_gateway import MCPGateway
    _GATEWAY: Optional[Any] = MCPGateway()
except Exception:  # pragma: no cover
    _GATEWAY = None


def call(claims: Dict[str, Any], tool: str, args: Dict[str, Any],
         approval: Optional[Dict[str, Any]] = None) -> Any:
    if _GATEWAY is None:
        raise RuntimeError("MCP gateway unavailable; install platform_core.")
    return _GATEWAY.invoke(user_claims=claims, agent_id=AGENT_ID, tool=tool, args=args, approval=approval)
