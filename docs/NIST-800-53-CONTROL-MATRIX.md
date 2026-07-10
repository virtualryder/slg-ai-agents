# NIST SP 800-53 Rev. 5 — Control Implementation Matrix

*Agentic-AI-relevant controls for the SLG accelerator. This is a control-assessment aid, not an ATO package — it shows how each control is implemented in this repo, what is inherited from AWS, and what the customer must own. Status: **Implemented** (in this repo, with evidence) · **Configurable** (customer wires/tunes) · **Customer** (customer-owned) · **Inherited** (AWS authorized service).*

| Control | Title / enhancement | Implementation here | Owner | Evidence | Status |
|---|---|---|---|---|---|
| **AC-2** | Account Management | Cognito user pool; admin-create; immutable role claim | Customer/Partner | `security.yaml`, golden-path `template.yaml` | Configurable |
| **AC-3** | Access Enforcement | Deny-by-default gateway authorization | Repo | `mcp_gateway/policy.py`, `test_mcp_gateway.py` | Implemented |
| **AC-3(7)** | Role-Based Access Control | Authorization keyed to `custom:slg_role` from a verified token | Repo | `jwt_verify.verified_roles`, `policy.py` | Implemented |
| **AC-4** | Information Flow Enforcement | VPC + Bedrock VPC endpoint; no PII egress; data-class isolation | Partner/Customer | `network.yaml`, `THREAT-MODEL.md` | Configurable |
| **AC-6** | Least Privilege | **Intersection** agent grant ∩ user entitlement; per-function IAM; Bedrock scoped to model+guardrail ARNs | Repo | `policy.py`, `security.yaml`, golden path | Implemented |
| **AC-6(1)** | Authorize Access to Security Functions | Consequential actions withheld in code; high-risk needs approver | Repo | `test_consequential_actions_withheld_from_agents` | Implemented |
| **AU-2** | Event Logging | Every tool attempt (allow/deny/pending/error) recorded | Repo | `mcp_gateway/audit.py` | Implemented |
| **AU-3** | Content of Audit Records | user, agent, tool, lineage, approver, timestamp, decision | Repo | `audit.py` record schema | Implemented |
| **AU-9** | Protection of Audit Information | **Append-only**: conditional PutItem + IAM Update/Delete deny; WORM | Repo | `audit_sinks.py`, `data.yaml`, `test_audit_append_only.py` | Implemented |
| **AU-10** | Non-Repudiation | Scoped token binds action to a named user; approver bound into record | Repo | `tokens.py`, `approvals.py` | Implemented |
| **AU-11** | Audit Record Retention | S3 Object Lock (WORM) retention by data class | Customer | `data.yaml` (records-schedule input) | Configurable |
| **CM-7** | Least Functionality | Deny-by-default `TOOL_REGISTRY` allowlist (no arbitrary tool) | Repo | `policy.py` | Implemented |
| **IA-2** | Identification & Authentication | Cognito JWT; cryptographic verification | Repo/Customer | `jwt_verify.py`, `test_jwt_verify.py` | Implemented |
| **IA-2(1)** | MFA | Cognito MFA ON; advanced security ENFORCED | Customer | `security.yaml`, golden path | Configurable |
| **IA-5** | Authenticator Management | KMS-held signing keys (prod); rotation; JWKS | Customer | `INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` | Configurable |
| **IA-8** | Non-Org Users (residents) | Federated IdP / Cognito for constituent identity | Customer | `security.yaml` | Configurable |
| **SC-7** | Boundary Protection | CloudFront + WAF + Shield; private subnets | Partner/Customer | `edge.yaml`, `network.yaml` | Configurable |
| **SC-8** | Transmission Confidentiality | TLS everywhere; WORM bucket TLS-only policy | Repo/Inherited | `data.yaml` `DenyInsecureTransport` | Implemented |
| **SC-12/13** | Cryptographic Key Mgmt / Protection | KMS CMK per data class; rotation | Customer | `security.yaml`, IR/KMS doc | Configurable |
| **SC-28** | Protection of Information at Rest | KMS SSE on DynamoDB + S3 | Repo | `data.yaml` | Implemented |
| **SI-4** | System Monitoring | CloudTrail · GuardDuty · Security Hub · Config · X-Ray | Customer | `THREAT-MODEL.md` §2 | Configurable |
| **SI-10** | Information Input Validation | Bedrock Guardrails (input); JWT/token/approval validation; request-hash binding | Repo | `security.yaml`, `tokens.py`, `approvals.py` | Implemented |
| **SI-15** | Information Output Filtering | Guardrails (output prompt-attack HIGH), **fail-closed** — a configured output guardrail that errors blocks + emits a `guardrail_failclosed` security event; grounded/cited outputs; fail-closed masking | Repo | `security.yaml`, `pii.py`, `infra/golden-path-311/guardrail-failclosed-alarm.yaml` | Implemented |
| **RA-5** | Vulnerability Monitoring | `bandit`/`pip-audit`/`checkov`/`semgrep` in CI; `pip-audit` is **BLOCKING** against the hash-pinned lockfile | Repo | CI, `CONTRIBUTING.md` | Implemented (pip-audit/bandit blocking) |
| **IR-4/6/8** | Incident Handling / Reporting / Plan | IR plan + regulatory notification matrix | Customer | `INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` | Configurable |
| **CA-7** | Continuous Monitoring | Security Hub + Config + audit analytics | Customer | `THREAT-MODEL.md` | Customer |
| **PT / AI-specific** | AI risk management | Grounding, prompt registry, evals, red team, fairness, HITL gates (NIST AI RMF) | Repo | `governance/` | Implemented |

## How to use this
- **Authorizing Official / Assessor:** treat "Implemented" rows as testable now (run the cited test or open the cited file); "Configurable/Customer" rows are the engagement and ATO scope.
- **Inheritance:** physical/environmental, and the underlying authorized services (Bedrock FedRAMP High / DoD IL-4/5 in GovCloud, KMS, DynamoDB, S3), are inherited from AWS.
- **Gaps to authorization:** live-connector testing, pen test, model-risk validation, DR test, and the StateRAMP/ATO package itself — see `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

*Prior high-level regime view: `docs/COMPLIANCE-CONTROL-MAPPINGS.md`. This matrix supersedes it for control-by-control assessment.*
