"""
Governed connector Lambda — the DEPLOYED MCP gateway enforcement point.

This is the single backend the HTTP tool route (`POST /tool/{kind}/{method}`)
invokes. It does **not** call the connector directly. Every request runs through
the deny-by-default authorization gateway IN-PROCESS, so the deployed path enforces
the same controls as the reference logic:

  verified JWT claims (from the API Gateway Cognito JWT authorizer)
    -> MCPGateway.invoke():
         * deny-by-default policy (agent grant ∩ user entitlement; unknown tool = DENY)
         * human-approval gate (bound, single-use, separation-of-duties) for high-risk tools
         * mint a scoped, request-bound, single-use token
         * invoke the agency connector (fixture | live)
         * append-only audit (DynamoDB conditional write when AUDIT_TABLE is set)
    -> decision-mapped HTTP status: ALLOW 200 / DENY 403 / PENDING_APPROVAL 202 / ERROR 500

Identity is taken ONLY from the authorizer-verified claims, never from the request
body. The route therefore cannot reach a system of record without passing the gate.
"""
from __future__ import annotations

import json
import os

# platform_core + governance are provided by the Lambda layer (or PYTHONPATH).
from slg_agent_platform.mcp_gateway import MCPGateway
from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog

_STATUS = {"ALLOW": 200, "DENY": 403, "PENDING_APPROVAL": 202}


def _build_gateway() -> MCPGateway:
    """Gateway whose audit writes to the append-only DynamoDB table when configured."""
    table = os.getenv("AUDIT_TABLE")
    sink = None
    if table:
        try:  # boto3 is present in the Lambda runtime; absent in local/unit tests
            from slg_agent_platform.mcp_gateway.audit_sinks import DynamoDBAppendOnlySink
            sink = DynamoDBAppendOnlySink(table)
        except Exception:  # pragma: no cover - fall back to in-memory audit
            sink = None
    return MCPGateway(audit=GatewayAuditLog(sink=sink))


def _claims(event):
    # HTTP API JWT authorizer places verified claims here. NEVER trust the body for identity.
    rc = event.get("requestContext") or {}
    authz = rc.get("authorizer") or {}
    jwt = authz.get("jwt") or {}
    return jwt.get("claims") or authz.get("claims") or event.get("claims") or {}


def _body(event):
    b = event.get("body")
    if isinstance(b, str):
        try:
            return json.loads(b or "{}")
        except Exception:
            return {}
    return b or {}


def _resp(status, payload):
    return {"statusCode": status, "headers": {"content-type": "application/json"},
            "body": json.dumps(payload)}


def handler(event, _ctx=None):
    try:
        path = event.get("pathParameters") or {}
        kind = path.get("kind") or event.get("kind")
        method = path.get("method") or event.get("method")
        if not kind or not method:
            return _resp(400, {"error": "missing tool kind/method"})

        body = _body(event)
        args = body.get("args", event.get("args", {})) or {}
        approval = body.get("approval", event.get("approval"))
        claims = _claims(event)
        agent_id = os.getenv("AGENT_ID") or body.get("agent_id") or event.get("agent_id") or "unknown"

        gw = _build_gateway()
        r = gw.invoke(user_claims=claims, agent_id=agent_id, tool=f"{kind}.{method}",
                      args=args, approval=approval)
        out = {"decision": r.decision, "audit_id": r.audit_id, "tool": r.tool, "reason": r.reason}
        if r.decision == "ALLOW":
            out["result"] = r.result
        return _resp(_STATUS.get(r.decision, 500), out)
    except Exception as exc:  # fail closed on any error (no result leaks)
        return _resp(500, {"decision": "ERROR", "error": type(exc).__name__})
