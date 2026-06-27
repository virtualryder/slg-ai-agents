# Second Independent Review — Findings & Improvement Backlog

*Date logged: 2026-06-26. Source: a second external (ChatGPT) review after P0–P4 + the post-review gateway fix. This review is **more favorable** and **more precise** than the first; it correctly identifies that the repo's strongest controls live in library code/tests and that the **deployed execution path must route through them**. We log every point here with an honest status so the gap between "control available" and "control integrated" stays visible.*

> **Timing note:** two of this review's headline items — the **deployed gateway bypass** and the **connector not parsing the API Gateway event** — were **fixed in the commit immediately before this review was written** (see `aws-native-reference/_shared/connector/handler.py` and `platform_core/tests/test_connector_gateway.py`). They are marked **DONE (post-review)** below; the reviewer was looking at the prior state.

## Updated scorecard (reviewer)
| Area | Earlier | Current |
|---|---|---|
| SLG use-case strategy | 9 | 9 |
| Executive / seller materials | 8 | 9 |
| Security architecture design | 7 | 8.5 |
| Security control library | 5 | 7.5 |
| Documentation & evidence package | 6 | 8.5 |
| Pilot accelerator readiness | 6 | 7 |
| Integrated deployment completeness | 3 | 4.5 |
| Production security readiness | 3–4 | 4 |
| Turnkey production readiness | 2–3 | 3–4 |

**Reviewer's core thesis:** *"The code that demonstrates strong security and the code that is actually deployed are not yet the same execution path."* The right next step is **one fully integrated, AWS-tested request** — not another doc, deck, agent, or matrix.

---

## Remaining weaknesses → backlog (with honest status)
Status key: **DONE** · **PARTIAL** · **OPEN**.

| # | Finding | Status | What's done / what remains |
|---|---|---|---|
| R2-1 | Deployed HTTP route bypassed the policy/approval/token/audit gateway | **DONE (post-review)** | `handler.py` now runs `MCPGateway.invoke()` in-process; deny-by-default + bound approval + scoped token + append-only audit; identity from the JWT authorizer only. Proof: `test_connector_gateway.py` (5 tests). |
| R2-2 | Connector didn't parse the API Gateway event (`event["kind"]` → KeyError) | **DONE (post-review)** | `handler.py` reads `pathParameters`, `requestContext.authorizer.jwt.claims`, and the JSON `body`; falls back to flat shape for local tests. |
| R2-3 | The "real agent" Lambdas don't call Bedrock | **PARTIAL (311 reference)** | `reasoning.py` (boto3-direct Bedrock Converse + ApplyGuardrail, **deterministic fallback** default so CI stays offline). 311 `draft.py` generates the grounded answer via **Bedrock + the deployed Guardrail** when `LLM_MODE=bedrock`; `check.py` re-applies the Guardrail to the output. Proof: `test_reasoning.py` (5). **KB/RAG done (311):** a new **Retrieve** step calls `kb.search_policy` THROUGH the gateway (governed, audited read), live mode backed by an **Amazon Bedrock Knowledge Base** (`LiveKbConnector`, `RetrieveFn` + `bedrock:Retrieve` + `KnowledgeBaseId`); `test_kb_retrieval.py` (6). **Propagated to ALL 8 agents:** every workflow runs Classify→**Retrieve** (governed `kb.search_policy`)→**Draft** (Bedrock+Guardrail, deterministic fallback)→**Check** (grounding+output guardrail); `test_workflow_agents_retrieval.py` (14). **Remaining:** keep classify deterministic (routing); live system-of-record connectors. |
| R2-4 | The Step Functions workflow never calls the connector/gateway | **DONE (all 8 agents)** | `finalize.py` now runs `MCPGateway.invoke()` for the consequential write (policy + bound approval + scoped token + connector create); ASL `ResultPath:$.approval` carries the reviewer's bound token into Finalize; `OutputPath:$.body` fixes the envelope chaining. Proof: `test_workflow_311_governed.py` (5) + `test_workflow_agents_governed.py` (14, agents 02–08). Each agent routes its own write tool (idp.assemble_form, permitting.create_application, eligibility.create_application/generate_notice, records.assemble_package, procurement.draft_rfp, itsm.create_ticket, safety.draft_report); the withheld consequential actions (issue_permit/adjudicate/release/award/run_runbook-for-analyst) stay denied. **311 also runs a governed READ** (`kb.search_policy` via the Retrieve step), so the workflow now touches a system of record through the gateway on both read and write. |
| R2-5 | The deployed workflow doesn't write the case audit record | **DONE (all 8 agents)** | every agent's `finalize.py` gateway call writes the append-only audit; the case carries the returned `audit_id`. |
| R2-6 | Smoke test bypassed auth + used a simple approval + didn't fail | **PARTIAL** | 311 smoke now mints a **bound, SoD approval** via a reviewer stand-in (`mint_approval.py`) and **exits non-zero** on failure, asserting the write went through the gateway. Still bypasses Cognito/API — the full authenticated-API negative-test suite is **P9**. |
| R2-7 | Secure infra (VPC/KMS/WORM/edge) and the working app are in two separate stacks | **OPEN** | Nest `network.yaml`/`security.yaml`/`data.yaml`/`edge.yaml` into the SAM golden path (or vice-versa) so **one command deploys the architecture the diagrams show** (private subnets, Bedrock VPC endpoint, CMK, Object Lock, WAF). |
| R2-8 | The 8 golden paths are cloned skeletons; high-sensitivity classes need materially different controls | **PARTIAL** | **Guardrails are now data-class-tuned** (CJI/FTI/PHI/secrets) and approver roles differ. Still to differentiate per class: account/VPC boundaries, KMS key policy, retention, identity assurance (AAL), session controls, IR procedures. |
| R2-9 | CI runs only `platform_core`+`governance` tests; several gates advisory; no dependency lockfile or cloud integration | **PARTIAL** | CI exists (tests, cfn-lint, bandit hard; semgrep/pip-audit/checkov advisory; TruffleHog; SBOM). Add: all-agent + WoG suites, a `sam build` per golden path, a lockfile, an **ephemeral-AWS integration job**, blocking severity thresholds, branch protection, signed/versioned releases. **No public GitHub Actions run has been demonstrated yet.** |
| R2-10 | Some architecture wording still overstates ("in-account inference," "data never leaves the VPC," "real agents," "complete architecture") | **DONE** | Narrowed in `README.md` (see below): Bedrock via **PrivateLink** (private connectivity to the regional service, not in-VPC hosting); golden-path workflow described as a **deployable deterministic skeleton**; "deny-by-default" framed as enforced at the connector enforcement point. |

---

## Recommended delivery phase (reviewer Priorities 1–5 → our P5–P9)
This is a **delivery-engineering phase**, not documentation. It is what moves the repo from "unit-tested reference" to "integration-tested pilot kit."

- **P5 — Integrate the control plane into the workflow** (R2-4, R2-5): ✅ **DONE for all 8 agents** — each `finalize.py` runs its write through the gateway (+ append-only audit), ASLs fixed (`OutputPath:$.body` + `ResultPath:$.approval`), per-agent bound-approval smoke tests. 19 workflow tests. **Remaining for full functional reality:** P6 (Bedrock in draft/check), P7 (real reviewer service), P8/P9.
- **P6 — Make one agent functionally real** (R2-3): ✅ **311 reasons with Bedrock AND grounds with governed RAG** — draft/check use Bedrock + the deployed Guardrail (deterministic fallback); a **Retrieve** step calls `kb.search_policy` through the gateway, backed by a Bedrock Knowledge Base in live mode. ✅ **Now propagated to ALL 8 agents** (`test_workflow_agents_retrieval.py`, 14). **Remaining:** live system-of-record connectors.
- **P7 — Real reviewer service** (R2-6 approval): a small service that authenticates the reviewer, checks entitlement + separation of duties, shows the exact action/args, mints the **bound** approval token, and audits the decision (no execution-history scraping).
- **P8 — Combine secure infra + app into one deploy** (R2-7): one `sam deploy` (or nested stacks) stands up VPC + endpoint + CMK + WORM + edge + gateway + agent + alarms.
- **P9 — Publish verified cloud evidence** (R2-6, R2-9): an ephemeral-AWS pipeline that deploys, runs authenticated API negative-tests (unauthorized tool denied, write needs approval, replay fails, audit exists, fixture request created), then tears down — and a first tagged release.

When **P5–P9** land and an AWS integration test is green, the package changes category. Until then, position it exactly as the reviewer recommends: *a strong governed SLG agent reference architecture and implementation accelerator with deployable workflow scaffolds* — **not** eight complete, secure, end-to-end production agents.

## Seller / deck guardrail (apply verbatim)
> **Customer-use classification:** Open-source **reference accelerator** for discovery, architecture workshops, and **synthetic-data pilots**. It is **not** an AWS service, not AWS-supported software, not a compliance certification, and **not ready for live government data** without customer-specific engineering, integration, testing, and authorization.
