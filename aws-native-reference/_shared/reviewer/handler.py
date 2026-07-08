"""
Reviewer Lambda — the DEPLOYED human-approval service (P7).

Sits behind the same Cognito-JWT HTTP API as the governed connector. A reviewer's identity
comes ONLY from the authorizer-verified JWT claims (never the body). Routes:

  GET  /approvals                         -> the reviewer's actionable queue (authority + SoD filtered)
  POST /approvals/{approval_id}/decision  -> {"decision":"approve"|"reject","comment":"..."}

On approve the service mints the bound token SERVER-SIDE (the reviewer never holds the
signing key), resumes the paused Step Functions execution (SendTaskSuccess), and writes the
decision to the append-only audit table; on reject it ends the execution (SendTaskFailure).
This replaces the mint_approval.py stand-in, which required the raw token secret.
"""
from __future__ import annotations

import hmac
import json
import os

from slg_agent_platform.mcp_gateway.audit import GatewayAuditLog
from slg_agent_platform.reviewer import ReviewerService, ReviewerError
from slg_agent_platform.reviewer.service import _Boto3StepFunctions
from slg_agent_platform.reviewer.store import DynamoDBPendingStore, ClaimConflict


def _origin_verified(event) -> bool:
    """Origin cloaking (secure variants): when ORIGIN_VERIFY_SECRET is set, require the
    X-Origin-Verify header CloudFront injects toward the origin, so the raw execute-api
    URL cannot be called around CloudFront/WAF. No-op when unset (base variants)."""
    secret = os.getenv("ORIGIN_VERIFY_SECRET", "")
    if not secret:
        return True
    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    return hmac.compare_digest(headers.get("x-origin-verify", ""), secret)


def _claims(event):
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


def _service():
    store = DynamoDBPendingStore(os.environ["PENDING_TABLE"])
    audit = GatewayAuditLog()
    table = os.getenv("AUDIT_TABLE")
    if table:
        try:
            from slg_agent_platform.mcp_gateway.audit_sinks import DynamoDBAppendOnlySink
            audit = GatewayAuditLog(sink=DynamoDBAppendOnlySink(table))
        except Exception:  # pragma: no cover
            pass
    return ReviewerService(store, sfn=_Boto3StepFunctions(), audit=audit)


def handler(event, _ctx=None):
    try:
        if not _origin_verified(event):
            return _resp(403, {"error": "origin verification failed"})
        claims = _claims(event)
        if not claims.get("sub"):
            return _resp(401, {"error": "unauthenticated"})
        method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") \
            or event.get("httpMethod", "GET")
        path = event.get("pathParameters") or {}
        svc = _service()

        if method.upper() == "GET":
            return _resp(200, {"pending": svc.list_pending(claims)})

        approval_id = path.get("approval_id") or _body(event).get("approval_id")
        if not approval_id:
            return _resp(400, {"error": "missing approval_id"})
        body = _body(event)
        out = svc.decide(claims, approval_id, body.get("decision", ""),
                         comment=body.get("comment", ""))
        # don't leak the raw token back over the API — it has already resumed the execution
        out.pop("token", None)
        return _resp(200, out)
    except ReviewerError as exc:
        return _resp(403, {"error": str(exc)})
    except ClaimConflict as exc:
        return _resp(409, {"error": str(exc)})
    except Exception as exc:  # fail closed
        return _resp(500, {"error": type(exc).__name__})
