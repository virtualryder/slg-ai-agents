# Security Policy

## Status & scope
This repository is a **governed reference accelerator** for State & Local Government (SLG) agentic AI on AWS. It is **not** an AWS-authorized or ATO/StateRAMP/FedRAMP-certified production system. The Python control plane is a **reference implementation** of the authorization, approval, token, audit, and masking semantics; production deployments substitute the managed AWS equivalents (Amazon Bedrock AgentCore Gateway/Identity, API Gateway + Cedar/Verified Permissions, STS, KMS, DynamoDB, S3 Object Lock). See `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

## Reporting a vulnerability
Report suspected vulnerabilities privately to the maintainer: **ryderdavid75@gmail.com** (subject: `SECURITY — slg-ai-agents`). Please include affected file/commit, reproduction, and impact. Do **not** open a public issue for an unfixed vulnerability. Target response: acknowledgement within 5 business days; triage and remediation plan within 15 business days. Coordinated disclosure is appreciated.

## What is in scope
- The Python control plane (`platform_core/`, `governance/`, `aws-native-reference/`).
- Infrastructure-as-code (`infra/`) — CloudFormation, SAM (golden path), Terraform.
- The deny-by-default authorization model, human-approval gate, scoped tokens, append-only audit, and PII/CJI/FTI masking.

## What is out of scope (customer/deployer responsibility)
- The customer's identity provider (IdP) federation and entitlement source of truth.
- Live connectors to systems of record (311/CRM, eligibility, Accela/Tyler, ECMS, ServiceNow).
- ATO / StateRAMP / FedRAMP authorization, third-party penetration testing, and continuous monitoring.
- Production secret material (KMS keys, token-signing keys), retention schedules, and DR.

## Security model (summary)
Defense in depth, fail-closed by default:
1. **Cryptographic identity** — RS256/JWKS JWT verification (`platform_core/slg_agent_platform/jwt_verify.py`); client-supplied roles are never trusted.
2. **Deny-by-default authorization** — least privilege as an intersection of agent grant ∩ user entitlement (`mcp_gateway/policy.py`).
3. **Bound human approval** — single-use, separation-of-duties, tamper-evident approval tokens for consequential actions (`mcp_gateway/approvals.py`).
4. **Scoped, short-lived tokens** — per-call, request-bound, single-use (`mcp_gateway/tokens.py`).
5. **Append-only audit + WORM** — conditional writes + IAM Update/Delete deny + S3 Object Lock (`mcp_gateway/audit_sinks.py`, `infra/cloudformation/data.yaml`).
6. **Fail-closed PII/CJI/FTI masking** (`pii.py`); **Bedrock Guardrails** on input and output.
7. **In-account inference** — Bedrock via VPC endpoint; no constituent-data egress.

Full threat model: `docs/THREAT-MODEL.md`. Control-to-NIST mapping: `docs/NIST-800-53-CONTROL-MATRIX.md`. OWASP LLM / MITRE ATLAS mapping: `docs/OWASP-LLM-ATLAS-MAPPING.md`. Incident response & key management: `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`.

## Supported versions
Pre-1.0 reference accelerator: only the latest `main` is supported. See `CHANGELOG.md`.
