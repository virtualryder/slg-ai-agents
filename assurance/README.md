# SLG Agentic AI Suite — Auditor & GRC Assurance Packet

**Cover sheet and curated index for a state/local-government auditor, CISO review, or GRC
assessor.** This packet does not duplicate content — it points to the artifacts already in
this repository, organized under standard assurance headings. Links are relative to the
repository root.

---

## 1. Purpose & scope

Eight state/local/whole-of-government agents on the shared Aegis control plane, built on AWS.
This packet lets a reviewer answer a CJIS / IRS Pub 1075 / GovRAMP security questionnaire
directly from repository artifacts.

> **Honesty line.** This suite is a **reference accelerator, not an ATO'd product and not a
> compliance certification.** It ships control *design* and reference IaC. Authorization to
> operate (ATO/GovRAMP), CJIS/FTI control operation on live systems, and accountability for
> compliance are **customer-owned**. See the maturity matrix in [`../README.md`](../README.md)
> for Implemented vs. Configurable (customer-owned).

---

## 2. Architecture & data-flow diagrams

- SLG governed data flow (constituent PII, CJI, FTI) — [`../docs/diagrams/slg-data-flow.svg`](../docs/diagrams/slg-data-flow.svg) ([PNG](../docs/diagrams/slg-data-flow.png))
- MCP gateway authorization flow (shared control plane, deny paths) — [`../docs/diagrams/mcp-gateway-auth-flow.svg`](../docs/diagrams/mcp-gateway-auth-flow.svg) ([PNG](../docs/diagrams/mcp-gateway-auth-flow.png))
- Suite architecture (edge-to-data narrative) — [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- Platform architecture / why the MCP layer — [`../docs/WOG-PLATFORM-ARCHITECTURE.md`](../docs/WOG-PLATFORM-ARCHITECTURE.md), [`../docs/WHY-THE-MCP-LAYER.md`](../docs/WHY-THE-MCP-LAYER.md)

## 3. Threat model & abuse cases

- STRIDE threat model, abuse cases, threat → control → file — [`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md)

## 4. Control mappings (NIST 800-53, NIST AI RMF; CJIS / IRS 1075 / GovRAMP)

- NIST 800-53 control matrix — [`../docs/NIST-800-53-CONTROL-MATRIX.md`](../docs/NIST-800-53-CONTROL-MATRIX.md)
- Regime mappings: CJIS v6.0, IRS Pub 1075 (FTI), GovRAMP/FedRAMP, NIST AI RMF — [`../docs/COMPLIANCE-CONTROL-MAPPINGS.md`](../docs/COMPLIANCE-CONTROL-MAPPINGS.md)
- OWASP LLM Top-10 + MITRE ATLAS mapping — [`../docs/OWASP-LLM-ATLAS-MAPPING.md`](../docs/OWASP-LLM-ATLAS-MAPPING.md)
- Governance controls (code) — [`../governance/controls/`](../governance/controls/)

## 5. Identity, authorization & human-in-the-loop controls

- Deny-by-default MCP gateway, JWT + `custom:slg_role` claim re-validation, scoped per-call tokens — [`../docs/WHY-THE-MCP-LAYER.md`](../docs/WHY-THE-MCP-LAYER.md), [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- Consequential (human-gated) commit controls & red-team scenarios — [`../governance/redteam/`](../governance/redteam/), [`../governance/tests/`](../governance/tests/)

## 6. Data protection (encryption, masking, WORM audit, residency)

- Encryption / key management (KMS CMK per data class CJI/FTI/PII/public), WORM audit — [`../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`](../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md)
- Data-class isolation and masking — see [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- Residency: data stays in the agency's AWS account/region; residency guarantees are **customer-owned** (region pinning, CJIS-in-scope region selection, endpoint policy).

## 7. Deployment evidence

- Clean-account acceptance run — [`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)
- No standalone `DEPLOYED-AND-VALIDATED.md` in this repo — the deployment validation summary lives in [`../README.md`](../README.md) ("Validation update") and [`../docs/RELEASE.md`](../docs/RELEASE.md).

## 8. Security testing (pen-test, CI gates, SBOM)

- Pen-test scope: **not present as a standalone doc** — customer-owned; nearest equivalent is the threat model + incident-response docs above.
- CI security gates — [`../.github/`](../.github/) workflows; test suite via `pytest` (see [`../pytest.ini`](../pytest.ini))
- SBOM: not present as a static artifact — **customer-owned**, generated per build/release.
- Repo review & remediation plan (self-assessment) — [`../docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md`](../docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md)

## 9. Shared-responsibility / RACI

- Production-readiness & shared-responsibility split (reference vs. customer-owned) — [`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md)
- Incident response runbook — [`../runbooks/INCIDENT-RESPONSE.md`](../runbooks/INCIDENT-RESPONSE.md)

## 10. Known limitations & maturity

- Capability maturity matrix — [`../README.md`](../README.md) (§ "Capability maturity matrix")
- Suite status — [`../SUITE-STATUS.md`](../SUITE-STATUS.md)
- Repo review & remediation backlog — [`../docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md`](../docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md)

## 11. Contact & reporting

- Vulnerability reporting via **GitHub Security Advisories** (repository *Security* tab →
  *Report a vulnerability*) — see [`../SECURITY.md`](../SECURITY.md). Do not open public issues
  for security reports.

---

*Reference accelerator — not an AWS service, not AWS-supported software, not a compliance
certification, and not production-ready for regulated data without customer-specific
engineering, testing, authorization, and operational ownership.*
