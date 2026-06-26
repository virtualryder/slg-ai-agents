# Repository Review — Verified Assessment & Remediation Plan

*Date: 2026-06-26 · Owner: David Ryder · Status: P0–P3 CLOSED; P4 (CI + evidence pack) + Final closure remain*

An external reviewer assessed this repository as **"a strong architecture, governance, and pilot accelerator — but not yet a complete, customer-deployable AWS solution."** We independently **verified every specific technical finding against the actual source files**. This document records (1) what we confirmed, (2) the prioritized plan to close each gap, and (3) how each closure is verified.

> **Verification honesty:** "Verified" below means checked against the repository source (CloudFormation, Python, docs) and, where noted, against `cfn-lint` / `pytest` / security scanners run in CI. It does **not** mean deployed into a live AWS account — true production sign-off still requires a customer AWS environment, security testing, and an authorization (ATO/StateRAMP) process. That boundary is intentional and is stated in `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

---

## Part 1 — Verified findings (reviewer claim → our verdict → evidence)

| # | Reviewer finding | Verdict | Evidence in repo |
|---|---|---|---|
| 1 | Quickstart claims "new account → running agent" but doesn't deliver it | **CONFIRMED** | `infra/cloudformation/quickstart.yaml` nests network/security/data/edge/agent — **not** a gateway stack; `Edge` needs an `OriginDomain` from a separately-deployed gateway |
| 2 | Agent state machine is a placeholder Pass state | **CONFIRMED** | `agent-service.yaml` → `DefinitionString` is literally `{"StartAt":"Done","States":{"Done":{"Type":"Pass","End":true}}}` |
| 2b | …but real implementation exists | **NUANCE (in our favor)** | `aws-native-reference/01-resident-services-311/` has real `lambdas/{check,classify,draft,finalize,hitl_notify}.py`, `stepfunctions/resident_services.asl.json`, `_shared/connector/handler.py`, `_shared/runtime/{Dockerfile,serve.py}` — **not wired** into the quickstart |
| 3 | One over-broad IAM role; `bedrock:*` on `Resource: "*"` | **CONFIRMED** | `security.yaml` → single `AgentRole` assumable by `lambda+states+ecs-tasks`; policy allows `bedrock:InvokeModel,bedrock:ApplyGuardrail` on `Resource: "*"` |
| 4 | Audit table is not actually append-only | **CONFIRMED** | `data.yaml` `AuditTable` has PITR + KMS only; the deny on `UpdateItem/DeleteItem` is a **comment** deferred to an Org SCP; no conditional-write enforcement |
| 5 | WORM retention hard-coded (7yr COMPLIANCE) for all data classes | **CONFIRMED** | `data.yaml` `WormBucket` → `DefaultRetention: {Mode: COMPLIANCE, Days: 2555}` fixed |
| 6 | Gateway trusts caller-supplied claims (no crypto verification) | **CONFIRMED (by design, unenforced)** | `mcp_gateway/gateway.py` authenticates on `user_claims.get("sub")`; `auth.py` reads claims from context. Intent (edge verifies) is documented but nothing forces it |
| 7 | Human-approval check is illustrative, not enforceable | **CONFIRMED** | `gateway.py` `_approval_ok` only checks `approved` truthy + `reviewer.sub` present — no binding to tool/args/amount, no separation of duties, no expiry, no single-use |
| 8 | Scoped token is dev HMAC with per-process key | **CONFIRMED (acknowledged in code)** | `mcp_gateway/tokens.py` → `_SECRET = getenv("GATEWAY_TOKEN_SECRET", secrets.token_hex(32))`; HMAC-SHA256; no iss/aud/data-class/one-time-use |
| 9 | PII masking fails open | **CONFIRMED** | `pii.py` `_ml_mask` → `except Exception: return text` (returns original on failure) |
| 10 | Guardrail baseline; output prompt-attack = NONE; no grounding | **CONFIRMED** | `security.yaml` `ResidentGuardrail` → `PROMPT_ATTACK InputStrength HIGH, OutputStrength NONE`; no contextual-grounding filter despite description |
| 11 | Network egress broadly open via NAT default route | **CONFIRMED** | `network.yaml` private subnets route `0.0.0.0/0` → NAT; no egress allowlist / Network Firewall / endpoint policies |
| 12 | Portable gateway thin; `AuthorizerFnArn` unused; no logging/throttle/WAF | **CONFIRMED** | `gateway-portable.yaml` declares `AuthorizerFnArn` (never referenced); no Lambda invoke permission, access logs, throttling, WAF, request validation, or DLQ; dynamic `POST /tool/{kind}/{method}` route |
| 13 | Compliance mapping is executive-level, not a control-assessment package | **CONFIRMED** | `docs/COMPLIANCE-CONTROL-MAPPINGS.md` is a high-level regime→service matrix; no control-by-control implementation/evidence/test/owner rows |
| 14 | No CI; no SECURITY.md/CONTRIBUTING/CHANGELOG | **CONFIRMED** | no `.github/`; no `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md` at repo root |
| 15 | DR runbook aspirational vs. deployed | **CONFIRMED** | `data.yaml` deploys only audit + HITL tables + WORM bucket; DR runbook describes global tables / Aurora Global / multi-Region KMS not in standalone IaC |

**Overall verdict:** the review is **accurate, specific, and fair.** It is a strong governance/architecture/pilot accelerator with genuine reference-implementation depth, but the headline "deployable" language and several controls are reference-grade, not production-enforced. The package is **broader than it is deep** — exactly as stated. The correct response is the reviewer's: **make one golden path indisputably real, then harden, then evidence it** — not add a ninth agent.

---

## Part 2 — Remediation plan (close one at a time, each verified)

Acceptance criteria are written so each item is **objectively checkable**. Verification = `cfn-lint`, `pytest`, scanner output, or a named doc artifact.

### P0 — Align claims to reality *(fastest; highest credibility risk)* — ✅ **CLOSED 2026-06-26**
- [x] Removed/replaced "new account → running agent," "field-ready," "each deployable standalone with its own complete secure architecture," "append-only" (where unenforced).
- [x] Added repo-top **Status & Maturity** banner (`README.md`): reference accelerator for discovery/workshops/pilots, 311 is the deployable golden path, others are patterns.
- [x] Labeled the quickstart honestly as **BASELINE INFRASTRUCTURE SCAFFOLDING**; `data.yaml` now states the audit table is not yet enforced append-only; both cross-link this plan.
- **Verified:** `grep` for overclaim strings returns NONE; banner present in `README.md` and `quickstart.yaml`. ✔

### P1 — One true golden path: Resident Services / 311 *(make it real)* — ✅ **CLOSED 2026-06-26**
- [x] Built `infra/golden-path-311/template.yaml` (SAM) — the **gateway is wired into the deployable path** as an HTTP API with a **Cognito JWT authorizer**.
- [x] Uses the **real** `resident_services.asl.json` (human gate = `waitForTaskToken`) with the 5 real Lambdas + the connector Lambda; function ARNs passed via `DefinitionSubstitutions`. SAM auto-grants the API→Lambda invoke permission.
- [x] API Gateway **access logging** (CloudWatch) + **throttling** (burst/rate params); the unused `AuthorizerFnArn` pattern is replaced by a native JWT authorizer. *(JSON request-schema validation + WAF fold into P2 gateway hardening.)*
- [x] `smoke_test.sh` (start execution → wait on human gate → `SendTaskSuccess` → assert non-`BLOCKED_NO_APPROVAL`), `deploy.sh`, `destroy.sh`; `DEPLOY-GOLDEN-PATH.md`. Scaffolding templates + 311 runbook now point to the golden path.
- **Verified:** `cfn-lint` **clean (US partition)** on `template.yaml`; per-function least-privilege roles (draft→`bedrock:InvokeModel` on the model ARN only; check→`bedrock:ApplyGuardrail` on the guardrail ARN; finalize→`dynamodb:PutItem` on the audit table). Live deploy/smoke run in the SA/customer account (no account in CI). ✔

### P2 — Harden the control plane *(what a CISO inspects)* — ✅ **CLOSED 2026-06-26**
- [x] **IAM:** `security.yaml` split into `AgentRuntimeRole` (bedrock scoped to the **model + guardrail ARNs**, no `Resource:"*"`) and `StatesExecutionRole` (lambda:InvokeFunction on the agent's function-name prefix only); golden path has per-function roles.
- [x] **Append-only audit:** new `mcp_gateway/audit_sinks.py` — `AppendOnlyStore` (overwrite/mutation rejected) + `DynamoDBAppendOnlySink` (conditional `PutItem attribute_not_exists`, never Update/Delete); `data.yaml` adds an **audit-writer managed policy** granting `PutItem` only and **explicitly denying** `UpdateItem/DeleteItem/BatchWriteItem`. Tests in `test_audit_append_only.py`.
- [x] **Approval binding:** new `mcp_gateway/approvals.py` — token bound to requestor+agent+tool+canonical-args-hash+amount-limit+approver+expiry+single-use **nonce**; **separation of duties** (approver ≠ requestor) at mint AND verify. Gateway enforces it; `test_mcp_gateway.py` proves self-approval, replay, args-tamper, wrong-tool, expired, and unbound-reviewer are all rejected.
- [x] **Token:** `tokens.py` now binds `iss/aud/agency/env/data_class/req_hash` + single-use nonce; verify checks audience + request-hash. `test_tokens.py`.
- [x] **JWT verification module:** new `jwt_verify.py` — RS256 over JWKS with iss/aud/exp + **alg-confusion guard** (rejects `none`/HS*); `verified_roles()` takes roles only from a verified token. `test_jwt_verify.py` proves tamper/iss/aud/expiry/alg-none/unknown-kid fail.
- [x] **WORM:** `data.yaml` retention + mode are now parameters keyed to a `DataClass` input (no fixed 7-yr default); + a TLS-only bucket policy.
- [x] **Masking fail-closed:** `pii.py` `_ml_mask` redacts the whole field + emits a `pii_mask_failclosed` security event on failure (was: returned raw text). Opt-out is explicit `MASK_FAIL_CLOSED=0`. `test_pii.py`.
- [x] **Cognito:** MFA ON, advanced security ENFORCED, 14-char password policy, 15-min access/ID tokens, **immutable** `slg_role` (`security.yaml` + golden path). *(Enterprise SAML/OIDC federation = customer IdP wiring, documented.)*
- [x] **Gateway:** access logging + throttling + Lambda invoke permission (`gateway-portable.yaml` + golden path); **WAF at the CloudFront edge** (`edge.yaml`) since WAFv2 doesn't attach to HTTP APIs; the dynamic `/tool/{kind}/{method}` route is constrained by the **deny-by-default `TOOL_REGISTRY` allowlist** (unknown tools denied before any connector runs).
- **Verified:** **69 `platform_core`+`governance` unit tests pass** (incl. all new negative cases) under the repo's `importlib` mode; `cfn-lint` **clean (US partition)** on `security.yaml`, `data.yaml`, `gateway-portable.yaml`, `quickstart.yaml`, and the golden-path template. ✔

### P3 — Security package (CISO evidence) — ✅ **CLOSED 2026-06-26**
- [x] `SECURITY.md` (policy + vuln disclosure + scope), `CONTRIBUTING.md` (security-bar PR checklist), `CHANGELOG.md` (P0–P3 history).
- [x] `docs/THREAT-MODEL.md` — trust boundaries + data-flow diagram, STRIDE-per-boundary table, and 7 agentic abuse/misuse cases with why each fails.
- [x] `docs/OWASP-LLM-ATLAS-MAPPING.md` — OWASP LLM Top-10 (2025) + MITRE ATLAS techniques mapped to controls, with a worked indirect-prompt-injection example.
- [x] `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md` — IR phases + **regulatory notification matrix** (CJIS/FTI/PHI/state) + KMS key-management table.
- [x] `docs/NIST-800-53-CONTROL-MATRIX.md` — control-by-control (AC/AU/IA/SC/SI/RA/CM/IR + AI-RMF) with implementation / owner / **evidence (file or test)** / status columns.
- [x] README wires the security package into “Start here” and the CIO/CISO/Architect section (assessor pointer).
- **Verified:** all 7 artifacts exist and cross-link; matrix covers the agentic-relevant families with per-row evidence pointers. ✔

### P4 — CI/CD security pipeline + evidence package
- [ ] `.github/workflows/`: `pytest`, `cfn-lint`, `tflint`, `checkov`, `bandit`, `semgrep`, `pip-audit`, secret scan, SBOM (CycloneDX), license scan.
- [ ] Golden-path **customer evidence package**: architecture diagram, bill of materials, IAM matrix, control statements, test/scan evidence, cost estimate, accessibility results, known limitations, shared-responsibility matrix.
- **Verify:** CI green on a clean checkout; evidence package assembled under `deliverables/`.

### Final — Closure verification
- [ ] Re-run this finding list against the updated repo; mark each **CLOSED** with the commit/artifact and the verification command/output.

---

## Part 3 — How to position it *today* (for sellers/SAs, until P3–P4 land)

Present as a **governed SLG agent architecture + implementation accelerator** for discovery, architecture workshops, envisioning, and scoped pilots — now with **one fully wired golden path (311)** and a **hardened control plane**. Do **not** represent it as deployable-as-is to production, AWS-authorized, or StateRAMP/FedRAMP-authorized. Use real data only after the customer's own security engineering and authorization. This matches `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
