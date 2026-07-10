# Production-Readiness Gap Assessment & Shared-Responsibility Matrix
*For a customer architecture / security review board. This document states honestly what this accelerator IS, what gives you confidence to start, what still must be built and authorized before production, and — in a RACI-style matrix — exactly who owns each piece (AWS · Delivery Partner/SI · Customer Agency).*

> **Bottom line up front:** this is a **production-shaped accelerator, not a production-ready, authorized system.** It embeds the governance controls that are usually retrofitted (deny-by-default authorization, withheld consequential actions, a framework-enforced human gate, WORM audit, masking) — which materially de-risks and shortens the path to production. It does **not** ship live integrations, an ATO/GovRAMP authorization, or third-party security testing. Those are real work, owned primarily by the customer with delivery-partner support. **Do not deploy to a regulated, constituent-facing workflow without completing the Go-Live Checklist below.**

---

## 1. Maturity ladder — where each piece sits today
| Level | Meaning | What's here |
|---|---|---|
| **Documented** | Architecture & controls designed and written | All 8 agents, the WoG platform, compliance mappings, runbooks |
| **Demonstrated** | Runs end-to-end with deterministic fixtures, no API key | 236 automated tests; agent demos; the WoG saga `local_runner` |
| **Deployable-by-design** | IaC + container/native contracts exist; needs a customer AWS account | CloudFormation + Terraform (commercial & GovCloud); per-agent deploy runbooks |
| **Production-ready** | Live connectors, ATO/GovRAMP, pen test, CSV, IdP integrated, DR tested | **NOT yet — this is the engagement** |

---

## 2. Why it should give you confidence (green lights — verifiable today)
1. **Consequential actions are withheld in code, not just policy.** Issue-permit, adjudicate, release-records, and award are absent from the agents' grants and a passing automated test proves it. The single largest risk — an agent taking an irreversible action — is structurally prevented.
2. **The human gate is framework-enforced.** `interrupt_before` / Step Functions `waitForTaskToken`; no code path commits a high-risk write without a verified approver bound into the record.
3. **Least-privilege is provable.** Deny-by-default gateway with `agent grant ∩ user entitlement`; the agent can never exceed the employee it acts for; scoped per-call tokens; no standing service accounts.
4. **Tamper-evident audit + WORM + masking** are present in the IaC (append-only DynamoDB, S3 Object Lock, KMS CMK; PII/CJI/FTI masked at every boundary).
5. **Complete, standards-aligned AWS architecture** (CloudFront + WAF + Shield → Cognito JWT → VPC → Bedrock + Guardrails → WORM) with a control→regime mapping for CJIS, IRS 1075, HIPAA, FERPA, DPPA, ADA, GovRAMP, NIST AI RMF.
6. **No lock-in, reviewable.** The authorization logic is readable, testable Python; IaC ships as CloudFormation **and** Terraform.
7. **Honest engineering.** A maturity ladder, a compliance disclaimer, vendor-vs-peer-reviewed labels on ROI figures, and counter-evidence shown on-slide. Nothing here overclaims.

---

## 3. What must be done before go-live (the gaps — stated plainly)
These are **not defects** — they are the boundary of an accelerator. They are real, funded work.

- **Integrations are fixtures.** There are **no live connectors** to the 311/CRM, integrated eligibility system, Accela/Tyler permitting, ECMS/records, ServiceNow, GIS, etc. Each must be **built and validated** against the live system. *(This is typically the largest line item.)*
- **No ATO / GovRAMP authorization.** There is no authorization to operate. Achieving ATO (and GovRAMP/StateRAMP where required) is a customer-owned process measured in months.
- **No third-party security testing.** Penetration test, threat model, and a security architecture review are required. The Python gateway is a **reference model** of the authorization — production runs on AgentCore Gateway / API Gateway + Cedar, and that **real** authorizer must be tested, not just the analog.
- **CI security supply chain.** Add SAST/DAST, dependency/vulnerability scanning, and an SBOM. Treat the repo as a **template your team owns**, not a black-box dependency.
- **Model-risk validation.** The deterministic decision engines (eligibility, scoring) are referenced; the real ones are the customer's, requiring integration and validation under the agency's model-risk process (SR 11-7-style where applicable). Guardrails and prompt-injection resistance need red-teaming against **your** data and threat model.
- **Accessibility.** Deterministic WCAG checks exist; add **axe-core in CI + a manual screen-reader pass** for ADA Title II on AI-generated output.
- **DR proven, not just documented.** Run a region-failover game day against the RTO/RPO targets.
- **Identity & retention config.** IdP federation + role mapping to the HR system; WORM retention set to the agency's records schedule.
- **Day-2 operations.** Staff and SLA the human-approval (HITL) queue; stand up monitoring/alarms, on-call, and prompt/model change control.

---

## 4. Shared-Responsibility (RACI-style) Matrix
**Legend:** **O** = Owns / Accountable · **R** = Responsible (does the work) · **C** = Contributes / Consulted · **–** = n/a.
**Status:** *In repo* (implemented) · *Config* (deploy-time configuration provided) · *To build* (not in repo — engagement work).

| # | Capability / control | AWS | Delivery Partner (SI) | Customer (Agency) | Status |
|---|---|:---:|:---:|:---:|---|
| 1 | Cloud region & service authorizations (FedRAMP/IL, GovCloud) | **O** | – | C | AWS-provided |
| 2 | Org / landing zone / **data-class isolation** (CJI·FTI·PHI·EDU·public) | C | R | **O** | Config (patterns in repo) |
| 3 | Network: VPC, private subnets, **CloudFront + WAF + Shield**, Bedrock VPC endpoint | – | R | **O** | Config (`network.yaml`, `edge.yaml`) |
| 4 | KMS CMK per data class | – | R | **O** | Config (`security.yaml`) |
| 5 | Identity provider (Okta/Entra/Login.gov) | – | C | **O** | Customer-owned |
| 6 | Cognito federation + **role → `custom:slg_role`** mapping to HR | – | R | **O** | Config (`security.yaml`) |
| 7 | Agent workflows, MCP gateway, governance framework | – | R (extend) | C | **In repo** |
| 8 | **Connectors to systems of record (LIVE)** | – | **R** | **O** (grants access/APIs) | **To build** (fixtures today) |
| 9 | Bedrock model access + **Guardrail** config & tuning | C | R | **O** | Config (baseline in repo) |
| 10 | **ATO / GovRAMP / StateRAMP authorization** | C | C | **O** | **To do** (not in repo) |
| 11 | Compliance control mappings → agency control set | – | R | **O** (validates) | In repo (Config) |
| 12 | **Penetration test · threat model · security review** | C | R | **O** (accepts) | **To do** |
| 13 | CI security: SAST/DAST, dependency scan, **SBOM** | – | **R** | C | **To build** |
| 14 | AI governance: grounding, prompt registry, evals, red team, fairness | – | R (extend) | C | In repo |
| 15 | **Model-risk validation** + deterministic decision engines | – | C | **O** | **To do** (engine is customer's) |
| 16 | **Red-team Guardrails / prompt-injection** vs. customer data | C | R | **O** | To do |
| 17 | Accessibility: WCAG CI + **axe-core + manual screen-reader** | – | R | **O** | Partial in repo + To do |
| 18 | Append-only audit + **WORM retention schedule** | – | R | **O** (sets schedule) | Config (`data.yaml`) |
| 19 | Data classification & handling (CJI/FTI/PHI) | – | C | **O** | Customer-owned |
| 20 | **HITL approval queue** staffing & SLAs | – | C | **O** | To do (ops) |
| 21 | Monitoring/alarms, observability, on-call | C | R | **O** | Config (patterns) + To do |
| 22 | **DR** runbook + tested region failover (RTO/RPO) | C | R | **O** | Runbook in repo; **test To do** |
| 23 | Incident response + **regulatory notification** (FTI/CJI/PHI clocks) | C | C | **O** | Runbook in repo |
| 24 | Change control for prompt/model versions | – | R | **O** (approves) | In repo (prompt registry) |

> Read the matrix as the engagement scope: rows marked **To build / To do** with an **O** in the Customer column (and **R** with the Partner) are where the real project work and timeline live — especially **#8 live connectors**, **#10 ATO**, **#12 security testing**, and **#15 model-risk validation**.

---

## 5. Go-Live Checklist (gated — all must pass before regulated production)
- [ ] Data classes identified; isolation boundaries (accounts/VPCs) implemented — *Customer*
- [ ] IdP federated; `custom:slg_role` mapping verified end-to-end — *Customer / Partner*
- [ ] **Live connectors** built and validated against each system of record — *Partner / Customer*
- [ ] Bedrock Guardrail mandatory in prod (`ENVIRONMENT=production` fails closed without one); tuned + red-teamed — *Partner / Customer*
- [ ] **Penetration test + threat model + security review** passed; the real gateway/authorizer (not the Python analog) tested — *Partner / Customer*
- [ ] CI security: SAST/DAST, dependency scan, SBOM in place — *Partner*
- [ ] **ATO / GovRAMP** (as applicable) achieved or interim authorization documented — *Customer*
- [ ] Model-risk validation complete; deterministic decision engines integrated & validated — *Customer*
- [ ] Accessibility: axe-core CI green + manual screen-reader pass — *Partner / Customer*
- [ ] Audit append-only (SCP deny Update/Delete); **WORM retention = records schedule** — *Customer*
- [ ] **HITL queue** staffed with SLAs; approver-identity enforcement tested — *Customer*
- [ ] Monitoring/alarms live; on-call defined — *Customer / Partner*
- [ ] **DR game day** executed against RTO/RPO — *Customer / Partner*
- [ ] Incident-response + regulatory-notification runbooks reviewed and owned — *Customer*
- [ ] Change-control process for prompt/model versions agreed — *Customer / Partner*

---

## 6. Recommended phased path (with go/no-go gates)
1. **Phase 0 — Sandbox/demo (days):** run the repo's demos + tests; architecture & security review board reviews this document. *Gate: fund a pilot.*
2. **Phase 1 — Scoped pilot (weeks):** one **low-blast-radius** agent — **Resident Services/311 or IT service desk**, *not* Benefits or Public Safety first — in a sandbox account; one live connector; deterministic-mode for the rest. *Gate: security review + pen test scoped.*
3. **Phase 2 — Hardening (weeks–months):** live connectors, Guardrail tuning + red team, accessibility, CI security, DR game day, and the **ATO/GovRAMP path** started. *Gate: authorization + go-live checklist.*
4. **Phase 3 — Limited production:** non-sensitive data first, fully monitored, with the human gate staffed. *Gate: stable metrics + audit evidence.*
5. **Phase 4 — Expand:** agent by agent on the shared standalone baseline; adopt the WoG platform when cross-agency coordination is the goal.

---

## 7. The honest summary for a review board
**Confidence to start: high.** The controls a public-sector security function cares about most are present, tested, and honestly represented — which is exactly why it's a credible foundation and a de-risked starting point.
**Confidence to run in production today: not yet, and it doesn't claim to be.** Live integrations, authorization, third-party testing, and operational ownership are real, funded work — owned primarily by the customer with delivery-partner execution, per the matrix above. Treat this as the architecture and governance foundation your team owns and hardens — not a turnkey product.
