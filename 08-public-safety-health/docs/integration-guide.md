# Public Safety / Public Health Case & Report — Integration Guide

This agent calls only its granted tools through the gateway; method signatures are identical in fixture (demo/CI) and live mode, so **no agent code changes** between them. Implement the agency adapters in `platform_core/slg_agent_platform/connectors/live.py` or set `<KIND>_BASE_URL` for the bundled REST adapter.

**Systems:** Incident systems, governed data lake (Lake Formation), OpenSearch, KB. Identity is established at the edge (Cognito federating the agency IdP); verified claims (`sub`, `custom:slg_role`) are forwarded and authorized by the gateway. A user can never retrieve, through the agent, anything they could not retrieve themselves.
