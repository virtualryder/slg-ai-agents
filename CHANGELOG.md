# Changelog

All notable changes to this accelerator. Format loosely follows Keep a Changelog; pre-1.0.

## [Unreleased] — 2026-06-26 — Production-readiness remediation (P0–P3)
### Added
- **Deployed gateway enforcement (post-review fix):** the connector Lambda (`aws-native-reference/_shared/connector/handler.py`) now runs `MCPGateway.invoke()` **in-process** for every HTTP tool call — deny-by-default policy, bound human approval, scoped token, and **append-only DynamoDB audit** — instead of calling the connector directly. Identity is taken only from the API Gateway JWT-authorizer claims. `GatewayAuditLog` gained an append-only `sink`; all 8 golden paths grant the connector `dynamodb:PutItem` + an `AGENT_ID`. Proven by `platform_core/tests/test_connector_gateway.py` (5 tests).
- **Data-class-tuned Guardrails + agent-specific smoke approvals (all 8):** each golden path's Bedrock Guardrail now uses a PII entity set + denied topics matched to its data class (CJI for public safety, FTI/PHI for benefits, secrets for IT desk, vendor-financial for procurement, broad redaction for FOIA); smoke-test approvals use a domain-appropriate reviewer role.
- **Golden paths (all 8 agents):** `infra/golden-path-*/` — every agent is now one-command deployable (SAM), generated from the 311 reference; index in `infra/GOLDEN-PATHS.md`. cfn-lint clean on all 8.
- **Golden path (P1):** `infra/golden-path-311/` — a fully wired SAM app for Agent 01 (real Lambdas + Step Functions ASL with `waitForTaskToken` human gate, HTTP API + Cognito JWT authorizer + access logging + throttling, per-function least-privilege roles). `deploy.sh` / `smoke_test.sh` / `destroy.sh`.
- **Bound approvals (P2):** `mcp_gateway/approvals.py` — single-use, separation-of-duties, args-bound approval tokens. Wired into the gateway; negative-case tests added.
- **JWT verification (P2):** `jwt_verify.py` — RS256/JWKS with issuer/audience/expiry and alg-confusion guard.
- **Append-only audit (P2):** `mcp_gateway/audit_sinks.py` (conditional PutItem) + `data.yaml` audit-writer policy denying Update/Delete.
- **CI/CD security pipeline (P4):** `.github/workflows/ci.yml` (pytest · cfn-lint · bandit · semgrep · pip-audit · checkov · TruffleHog · CycloneDX SBOM) and a golden-path **customer evidence package** under `deliverables/golden-path-311-evidence/`.
- **Security package (P3):** `SECURITY.md`, `CONTRIBUTING.md`, this changelog; `docs/THREAT-MODEL.md`, `docs/OWASP-LLM-ATLAS-MAPPING.md`, `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`, `docs/NIST-800-53-CONTROL-MATRIX.md`.
- **Review & plan:** `docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` — independent review, verified findings, P0–P4 plan.
- README **"Start here"** guide and **CIO/CISO/Director-of-Architecture** section.

### Changed
- **Hardened scoped tokens (P2):** `tokens.py` now binds iss/aud/agency/env/data_class/request-hash + single-use.
- **Masking fails closed (P2):** `pii.py` redacts + emits a security event on ML-masking failure (was: returned raw text).
- **IAM split + scoped Bedrock (P2):** `security.yaml` splits runtime vs. Step Functions roles; Bedrock scoped to model + guardrail ARNs (no `Resource:"*"`). Guardrail prompt-attack now HIGH on input **and** output.
- **WORM by data class (P2):** `data.yaml` retention/mode parameterized by data classification; TLS-only bucket policy.
- **Cognito hardened:** MFA on, advanced security enforced, immutable role claim, 15-min tokens.
- **Honesty (P0):** removed "new account → running agent" / "field-ready" / "deployable standalone complete" claims; added Status & Maturity banner; test-count claims made factual.

### Security
- Replaced the illustrative `approved + reviewer.sub` approval check with an enforceable, bound, single-use, SoD-validated approval.
- Gateway no longer trusts client-supplied identity claims without cryptographic verification (reference module provided).

### Verification
- 69 `platform_core` + `governance` tests pass (no API key); `cfn-lint` clean (US partition) on all changed templates and the golden path.
