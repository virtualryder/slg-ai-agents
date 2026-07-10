# Threat Model — SLG Agentic AI on AWS

*Scope: the governed agent control plane and its golden-path deployment (Agent 01 / 311). Method: trust-boundary + data-flow analysis with STRIDE per boundary, plus agentic abuse/misuse cases. Companion: `OWASP-LLM-ATLAS-MAPPING.md`, `NIST-800-53-CONTROL-MATRIX.md`.*

## 1. Assets
- Constituent PII / CJI (criminal justice) / FTI (federal tax) / PHI; case and benefits data.
- The authority to take a **consequential action** (issue permit, adjudicate eligibility, release records, award contract).
- The audit trail (evidentiary; subject to records law and litigation hold).
- Secret material: KMS CMKs, token-signing keys, connector credentials.

## 2. Trust boundaries & data-flow
```
[ B0 Internet ]
   resident / staff browser, mobile, phone
        │  (1) HTTPS
        ▼
┌─ B1 AWS edge ───────────────────────────────────────────────┐
│  CloudFront + AWS WAF (OWASP managed rules, rate-limit) + Shield │
└────────┬────────────────────────────────────────────────────┘
         │ (2) HTTPS
         ▼
┌─ B2 Identity ───────────────────────────────────────────────┐
│  Amazon Cognito (federates agency IdP → signed JWT)          │
│  API Gateway JWT authorizer                                  │
└────────┬────────────────────────────────────────────────────┘
         │ (3) verified JWT claims only
         ▼
┌─ B3 Private VPC — agent runtime ────────────────────────────┐
│  Step Functions + Lambda (or AgentCore Runtime)             │
│  classify → draft → check → [HUMAN GATE] → finalize         │
│        │ (4) tool call                                       │
│        ▼                                                     │
│  B3a MCP authorization gateway                              │
│   • verify_jwt (RS256/JWKS, iss/aud/exp, alg guard)         │
│   • deny-by-default policy: agent grant ∩ user entitlement  │
│   • bound, single-use, SoD human-approval for high-risk     │
│   • mint scoped, request-bound, single-use token            │
│        │ (5) scoped token + args                             │
│        ▼                                                     │
│  B3b Bedrock (Claude) + Guardrails  ── via VPC endpoint ──► [no PII egress]
│  B3c Connector Lambda ─► systems of record (live) / fixtures │
└────────┬────────────────────────────────────────────────────┘
         │ (6) every attempt (allow/deny/pending/error), PII-masked
         ▼
┌─ B4 Data & evidence ────────────────────────────────────────┐
│  DynamoDB append-only audit (PutItem-only + Update/Delete deny, PITR)
│  S3 Object Lock (WORM), KMS CMK per data class               │
│  Cross-cutting: CloudTrail · GuardDuty · Security Hub · Config · X-Ray
└─────────────────────────────────────────────────────────────┘
```

## 3. STRIDE by boundary (threat → mitigation → evidence)
| Boundary | Threat (STRIDE) | Mitigation | Evidence |
|---|---|---|---|
| B1 edge | DoS / volumetric (D); injection probing (T) | WAF managed rules + rate-limit; Shield; API throttling | `edge.yaml`, golden-path `DefaultRouteSettings` |
| B2 identity | Spoofed identity / forged token (S/T); priv-esc via role claim (E) | Cognito JWT authorizer; RS256/JWKS verify; **roles only from verified token**; MFA; immutable `slg_role` | `jwt_verify.py`, `test_jwt_verify.py`, `security.yaml` |
| B3a gateway | Confused-deputy / over-reach (E); replay (T); approval forgery (T/R) | Deny-by-default intersection; **bound single-use SoD approvals**; scoped single-use tokens. **Enforced on the deployed HTTP route by the connector Lambda** (`handler.py` runs `MCPGateway.invoke` in-process). | `policy.py`, `approvals.py`, `tokens.py`, `test_mcp_gateway.py`, `test_connector_gateway.py` |
| B3b model | Prompt injection (T); sensitive disclosure (I); excessive agency (E) | Guardrails in+out (**output guardrail fails closed** — a configured guardrail that errors blocks + emits `guardrail_failclosed`); consequential actions withheld in code; human gate | `security.yaml` Guardrail, `policy.py`, `test_hitl_enforced.py`, `infra/golden-path-311/guardrail-failclosed-alarm.yaml` |
| B3c connector | SSRF / tool retargeting (T/E) | Deny-by-default `TOOL_REGISTRY` allowlist; scoped token bound to tool+args | `policy.py`, connector handler |
| B4 audit | Tamper / repudiation (T/R); data at rest (I) | Append-only (conditional write + Update/Delete deny); WORM; KMS; PII masked | `audit_sinks.py`, `data.yaml`, `test_audit_append_only.py` |
| Logs everywhere | PII leakage into logs (I) | **Fail-closed** masking at the log/audit boundary | `pii.py`, `test_pii.py` |

## 4. Agentic abuse / misuse cases (and why they fail)
1. **"Make the agent issue a permit."** The tool is absent from the agent's grants (withheld in code) → DENY, verified by test.
2. **"Reuse a screenshot of an approval to push a second write."** Approval token is single-use (nonce) and bound to the exact args → second attempt PENDING_APPROVAL.
3. **"Self-approve my own request."** Separation of duties: approver ≠ requestor, enforced at mint and verify.
4. **"Change the amount after approval."** Token is bound to a canonical args hash → request-hash mismatch → rejected.
5. **"Send a forged JWT with `custom:slg_role=benefits_supervisor`."** Signature fails against the JWKS; `alg:none` rejected; roles taken only from a verified token.
6. **"Indirect prompt injection in an uploaded document tells the agent to exfiltrate."** Guardrails + the agent has no exfiltration tool (deny-by-default), and any write is gated. Inference can't egress (VPC endpoint).
7. **"Flood the endpoint to run up Bedrock cost."** WAF rate-limit + API throttling + (customer) budget alarms; unbounded-consumption tracked in `OWASP-LLM-ATLAS-MAPPING.md` (LLM10).

## 5. Residual risk (customer-owned)
Live-connector security testing, IdP federation hardening, model-risk validation against the agency's data, Guardrail/red-team tuning, DR game-day, and the StateRAMP/ATO authorization remain customer engagement work (`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`). Egress allowlisting (Network Firewall) is a documented optional overlay.
