# Procurement, Contracting & Grants — Integration Guide

This agent calls only its granted tools through the gateway; signatures are identical in fixture and live mode (no agent code changes). Implement agency adapters in `platform_core/slg_agent_platform/connectors/live.py` or set `<KIND>_BASE_URL`.

**Systems:** ERP/e-procurement, grants systems, IDP, KB. Identity is established at the edge (Cognito federating the agency IdP); verified claims (`sub`, `custom:slg_role`) are forwarded and authorized by the gateway — least-privilege intersection `agent grant ∩ user entitlement`.
