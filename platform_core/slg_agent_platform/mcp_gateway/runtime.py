"""
Runtime gateway builder — one place that constructs an MCPGateway wired to the
deployed append-only audit table.

Both the HTTP connector Lambda and the Step Functions workflow Lambdas use this so
every governed tool call (whichever path it arrives on) lands in the same
append-only audit store. In the Lambda runtime boto3 is present and the sink is a
DynamoDB conditional PutItem; in local/unit tests boto3 is absent and the audit is
in-memory — the policy/approval/token decisions are identical either way.
"""
from __future__ import annotations

import os
from typing import Optional

from .audit import GatewayAuditLog
from .gateway import MCPGateway


def build_gateway(audit_table: Optional[str] = None) -> MCPGateway:
    table = audit_table or os.getenv("AUDIT_TABLE")
    sink = None
    if table:
        try:  # boto3 present in Lambda; absent in local/unit tests -> in-memory audit
            from .audit_sinks import DynamoDBAppendOnlySink
            sink = DynamoDBAppendOnlySink(table)
        except Exception:  # pragma: no cover
            sink = None
    return MCPGateway(audit=GatewayAuditLog(sink=sink))
