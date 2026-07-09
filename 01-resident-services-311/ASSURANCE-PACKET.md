# Assurance Packet — SLG Agent 01 (Resident Services / 311)

*One document, everything a director of architecture, a CISO, a records/privacy officer, or a
StateRAMP/CJIS assessor needs to evaluate this hero agent. Every claim links to code, a test, or
deployment evidence. Boundaries: [`NOT-CLAIMS.md`](../NOT-CLAIMS.md); machine-readable status:
[`MATURITY.yaml`](../MATURITY.yaml).*

> **What this is:** a governed reference accelerator agent, **not** an AWS service, not a compliance
> certification, not StateRAMP/FedRAMP-authorized. Reference accelerator for discovery, architecture
> workshops, and scoped, synthetic-data pilots.

---

## 1. At a glance

| | |
|---|---|
| **Agent** | 01 — Resident Services / 311 (classify a resident request → retrieve grounded policy → draft a response/service-request → **human review for any write** → create/update in the city system) |
| **Maturity** | **Deploy-validated** (all 8 golden paths + a hardened secure variant deployed, runtime-verified, torn down) |
| **Governance pattern** | Conforms to **Aegis Governance Pattern (AGP) v1.0** |
| **System of record** | NYC 311 Socrata — **tier-3 live reference connector** (public open data, read-only). ServiceNow/Salesforce 311 = **tier-4, not done** (engagement) |
| **Data class** | Public open data in the reference path (no PII). CJI/PII for a real deployment stays in separated, entitled environments |
| **Negative controls** | `make neg-demo` — **10/10 refusals enforced** (CI-gated) |

## 2. Architecture & diagrams

- **Suite / per-agent architecture:** [`docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md), per-agent runbook [`docs/DEPLOY-RUNBOOK.md`](docs/DEPLOY-RUNBOOK.md).
- **Data flow:** `docs/diagrams/slg-data-flow.svg`.
- **Deployment evidence (control-by-control):** [`deliverables/golden-path-311-evidence/CONTROL-EVIDENCE.md`](../deliverables/golden-path-311-evidence/CONTROL-EVIDENCE.md).
- **Trust boundaries (summary):**

```
  ┌──────────── Agency AWS account (per-agent VPC) ─────────────┐
  │  IdP/Cognito ─(verified JWT)→ [MCP AUTHORIZATION GATEWAY] ──┐│
  │    deny-by-default · least-privilege intersection ·        ││
  │    scoped short-lived token · fail-closed PII/CJI mask ·   ▼│
  │    append-only + S3 Object-Lock audit · token budget  [connector]
  │  Bedrock + Guardrails ◄─ PrivateLink (regional AWS)   (fixture / NYC311 r/o)
  └──────────────────────┬───────────────────────────────────┘
   no egress to external │ human reviewer approves any write (create/update SR)
   AI APIs               ▼
                 NYC 311 Socrata (public, read-only)   [tier-4 ServiceNow = NOT here]
```

Full trust-boundary + abuse cases: [`docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md).

## 3. MCP / tool authorization

Deny-by-default gateway: verified identity → **least-privilege intersection** (`permitted ⇔ tool ∈
agent_grant ∩ user_entitlement`) → human approval for writes → short-lived scoped token → fail-closed
PII/CJI mask → append-only audit. The agent may **create** a service request but is **not granted**
`crm311.update_service_request` (mutation is a city-system/human action), and consequential actions
(issue permit, adjudicate eligibility, release records, award contract) are withheld from every agent.
Reference logic: [`../platform_core/slg_agent_platform/mcp_gateway/`](../platform_core/slg_agent_platform/mcp_gateway/).

## 4. Control matrix (condensed)

| Control | Mechanism (code) | Evidence / test | Owner |
|---|---|---|---|
| Identity / authN | Verified IdP JWT (RS256/JWKS; alg-confusion guarded) (`jwt_verify.py`) | negative demo #1–2 | Repo (federated IdP = Customer) |
| Deny-by-default authz | Least-privilege intersection (`mcp_gateway/policy.py`) | negative demo #3–4 | Repo |
| Consequential actions withheld | issue_permit / adjudicate / release / award absent from agent grants | `policy.py` NOTEs + tests | Repo |
| Human approval (SoD) | Bound, single-use, args-bound tokens + NonceStore (`mcp_gateway/approvals.py`) | negative demo #5–7 | Repo |
| Scoped short-lived tokens | Per-call, tool + args-bound (`mcp_gateway/tokens.py`) | gateway tests | Repo |
| Fail-closed PII/CJI masking | Mask before any model/audit write (`pii.py`, `audit.py`) | negative demo #8 | Repo (runtime verify = Customer) |
| Append-only + WORM audit | DynamoDB append-only + S3 Object Lock | negative demo #9; clean-account run | Repo (retention config = Customer) |
| Token budget / cost control | Hard-cap preflight before spend (`budget.py`) | `test_budget.py`, negative demo #10 | Repo |
| Private-connectivity inference | Bedrock via PrivateLink; no egress to external AI APIs | `docs/THREAT-MODEL.md` | Repo/Customer |

Full mappings: [`docs/NIST-800-53-CONTROL-MATRIX.md`](../docs/NIST-800-53-CONTROL-MATRIX.md) ·
[`docs/OWASP-LLM-ATLAS-MAPPING.md`](../docs/OWASP-LLM-ATLAS-MAPPING.md).

## 5. Deployment evidence

All 8 golden paths were deployed to a **clean AWS account (us-east-1)**, runtime-verified (311 ran
Classify → Retrieve → Draft → Check → **paused at the human gate**, and the governed `kb.search_policy`
read wrote an append-only audit record), and torn down (zero residual `slg-*` resources). Proof:
[`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md) ·
[`deliverables/golden-path-311-evidence/`](../deliverables/golden-path-311-evidence/). The live run
caught two real bugs (Guardrail output-strength; Lambda path resolution) that cfn-lint and the offline
suite did not.

## 6. Negative-test results

`make neg-demo` → [`demo/negative_demo.py`](demo/negative_demo.py), CI-gated by
[`../governance/tests/test_negative_demo.py`](../governance/tests/test_negative_demo.py). Latest: **10/10 enforced**.

| # | Attempt | Result |
|---|---|---|
| 1 | No / missing JWT | **DENY** — no authenticated subject |
| 2 | Bad JWT (alg `none`) | **DENY** — RS256 required |
| 3 | Wrong role (not entitled) | **DENY** — agent may not exceed the human |
| 4 | Unregistered tool | **DENY** — unknown tool |
| 5 | Self-approval | **DENY** — separation of duties |
| 6 | Approval replay | **DENY** — single-use nonce consumed |
| 7 | Tampered args | **DENY** — args-hash mismatch |
| 8 | Masker unavailable | **FAIL-CLOSED** — no unmasked record |
| 9 | Audit sink unavailable | **FAIL-CLOSED** — no silent success |
| 10 | Over-budget call | **DENY** — hard cap, before spend |

## 7. Known limitations (read before a pilot)

- **Reference connector is public/read-only** (NYC 311 Socrata). A production 311 system (ServiceNow,
  Salesforce, a custom CRM) is **tier-4** engagement work; CJI-touching agents run in separated,
  entitled environments.
- **Not StateRAMP/FedRAMP-authorized, no ATO.** Those authorizations attach to the **AWS services** in
  GovCloud, not to this accelerator.
- **Federated IdP login not proven end-to-end**; masking is unit-tested, not runtime-verified on AWS.
- Benefits and Public Safety agents are high-blast-radius — **not** first pilots.

## 8. Shared-responsibility RACI (condensed)

| Area | Repo (accelerator) | Customer (engagement) |
|---|---|---|
| Governed control plane (authz, approval, tokens, audit, masking, budget) | **Owns** (code + tests) | Configures, operates, validates |
| IdP + entitlement source of truth | Enables | **Owns** |
| Production 311 connector (ServiceNow/Salesforce), CJI environments | Reference only | **Owns** |
| ATO / StateRAMP / pen test / monitoring / DR | — | **Owns** |
| KMS keys, WORM retention, secrets | Reference config | **Owns** |

Full matrix: [`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md).

---

*If any statement here reads as stronger than [`NOT-CLAIMS.md`](../NOT-CLAIMS.md) or
[`MATURITY.yaml`](../MATURITY.yaml), those files govern.*
