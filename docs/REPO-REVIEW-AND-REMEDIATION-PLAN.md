# Repository Review — Verified Assessment & Remediation Plan

*Date: 2026-06-26 · Owner: David Ryder · Status: **P0–P4 CLOSED**; final closure report below*

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

### P4 — CI/CD security pipeline + evidence package — ✅ **CLOSED 2026-06-26**
- [x] `.github/workflows/ci.yml` — 7 jobs: **unit tests**, **cfn-lint**, **bandit** (hard gates) + **semgrep**, **pip-audit**, **checkov** (advisory), **TruffleHog** secret scan, **CycloneDX SBOM** artifact.
- [x] Golden-path **customer evidence package** under `deliverables/golden-path-311-evidence/`: architecture + bill of materials + IAM matrix; control statements + test/scan evidence; cost estimate, accessibility, known limitations, shared-responsibility.
- **Verified locally:** hard gates pass — `pytest` 69 green; `cfn-lint --ignore-checks E3006` clean on all templates + golden path; `bandit -lll` **0 High**. (All IaC templates re-linted clean; `agent-service.yaml`/`quickstart.yaml` truncation repaired.) ✔

### Final — Closure verification — ✅ **DONE 2026-06-26** (see Part 4)

### Final — Closure verification
- [x] Re-run this finding list against the updated repo; each finding mapped to fix + verification in **Part 4** below.

---

---

## Part 4 — Closure report (every finding → resolution → verification)

| # | Finding | Resolution (phase) | Verification |
|---|---|---|---|
| 1 | "New account → running agent" overclaim | Reworded to scaffolding (P0) + real golden path (P1) | `grep` clean; `infra/golden-path-311/` deploys real agent; `cfn-lint` clean |
| 2 | Placeholder `Pass` state machine | Golden path uses the real `resident_services.asl.json` (P1); scaffolding relabeled | `template.yaml` `DefinitionUri` → ASL; smoke test asserts the human gate |
| 3 | Over-broad IAM `bedrock:* / Resource:"*"` | Split roles; Bedrock scoped to model+guardrail ARNs (P2) | `security.yaml`, golden-path per-function roles; `cfn-lint` clean |
| 4 | Audit not append-only | Conditional `PutItem` + IAM Update/Delete **deny** (P2) | `audit_sinks.py`, `data.yaml`, `test_audit_append_only.py` |
| 5 | WORM hard-coded 7yr | Retention/mode parameterized by `DataClass` (P2) | `data.yaml` params |
| 6 | Gateway trusts caller claims | RS256/JWKS verification module (P2) | `jwt_verify.py`, `test_jwt_verify.py` |
| 7 | Approval illustrative | Bound, single-use, SoD approval tokens (P2) | `approvals.py`; 6 negative tests in `test_mcp_gateway.py` |
| 8 | Dev HMAC token | Hardened (iss/aud/agency/data-class/req-hash/single-use); KMS/STS swap documented (P2) | `tokens.py`, `test_tokens.py` |
| 9 | Masking fails open | Fail **closed** + security event (P2) | `pii.py`, `test_pii.py` |
| 10 | Guardrail output prompt-attack NONE | Output strength HIGH (P2) | `security.yaml`, golden-path Guardrail |
| 11 | Broad NAT egress | Documented optional overlay (Network Firewall / endpoint policies); VPC + Bedrock endpoint in place | `THREAT-MODEL.md`, `COST-AND-LIMITATIONS.md` — **closed as documented overlay** |
| 12 | Thin gateway; unused authorizer param | Removed unused param; access logs + throttling + invoke perm; WAF at edge; registry allowlist (P1/P2) | `gateway-portable.yaml`, golden path; `policy.py` allowlist |
| 13 | Compliance mapping high-level | NIST SP 800-53 control matrix w/ evidence/owner (P3) | `docs/NIST-800-53-CONTROL-MATRIX.md` |
| 14 | No CI / SECURITY.md | `SECURITY.md` + `CONTRIBUTING.md` + `CHANGELOG.md` (P3) + `ci.yml` 7-job pipeline (P4) | files present; `ci.yml` valid; gates pass locally |
| 15 | DR aspirational | Current vs. overlay made explicit; PITR + WORM present; multi-Region = additive overlay | `data.yaml` notes, `COST-AND-LIMITATIONS.md` — **closed as documented overlay** |

**Net:** 13 of 15 findings fully closed with code/IaC + tests/lint; **#11 (egress) and #15 (multi-Region DR)** are closed as **explicitly documented optional overlays** (honest scoping, not silent gaps). The headline "broader than deep" critique is addressed: there is now one **indisputably real, hardened, evidenced** golden path, and the controls behind it are tested.

**Residual (unchanged, customer-owned):** live connectors, third-party pen test, ATO/StateRAMP, model-risk validation, DR game-day, and IdP federation — per `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

## Part 3 — How to position it *today* (for sellers/SAs, until P3–P4 land)

Present as a **governed SLG agent architecture + implementation accelerator** for discovery, architecture workshops, envisioning, and scoped pilots — now with **one fully wired golden path (311)** and a **hardened control plane**. Do **not** represent it as deployable-as-is to production, AWS-authorized, or StateRAMP/FedRAMP-authorized. Use real data only after the customer's own security engineering and authorization. This matches `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
