# Incident Response & Key Management

*Reference plans for a regulated SLG agent deployment. The agency's CISO owns the authoritative IR and KMS programs; this aligns the agent's controls to them. Companion: `THREAT-MODEL.md`, `runbooks/INCIDENT-RESPONSE.md` (ops).*

## Part A — Incident Response (NIST IR-4/IR-6/IR-8 aligned)

### Detection sources
- **CloudTrail** (control-plane API calls), **GuardDuty** (threat detection), **Security Hub** (findings), **Config** (drift), **X-Ray** (traces).
- **Audit trail** — every gateway decision (ALLOW/DENY/PENDING_APPROVAL/ERROR) with user, tool, lineage; spikes in DENY or PENDING are signals.
- **Security events** — fail-closed masking emits `pii_mask_failclosed`; approval/token rejections are logged.

### Phases
1. **Detect & triage** — classify severity by data class touched (CJI/FTI/PHI = highest) and whether a consequential action or data egress occurred.
2. **Contain** — disable the affected Cognito user/role; rotate the token-signing key (invalidates live scoped tokens); revoke connector credentials; tighten WAF; if needed, disable the agent's state machine.
3. **Eradicate** — patch the vulnerability; invalidate compromised approvals (nonce store / DynamoDB); review the append-only audit (immutable — tamper-evident) for scope.
4. **Recover** — restore from PITR / WORM evidence as needed; re-enable after verification; document.
5. **Post-incident** — root cause, control-gap update to `THREAT-MODEL.md` and the NIST matrix, lessons learned.

### Regulatory notification matrix (confirm exact timelines with counsel)
| Data class | Regime | Typical notification |
|---|---|---|
| CJI | CJIS Security Policy | Notify the CJIS Systems Officer (CSO) / FBI per state policy, without undue delay |
| FTI | IRS Pub 1075 | Notify IRS Office of Safeguards + TIGTA **within 24 hours** of a suspected incident |
| PHI | HIPAA Breach Notification | Individuals/HHS per breach rule (generally ≤ 60 days; state law may be stricter) |
| PII (state) | State breach-notification law | Per state statute (varies; often "without unreasonable delay") |
| Election/other | State-specific | Per agency policy |

> The append-only, WORM audit trail is the evidentiary backbone for any of the above — preserve it under legal hold before remediation.

## Part B — Key Management (NIST SC-12/SC-13/IA-5 aligned)
| Key / secret | Service | Rotation | Notes |
|---|---|---|---|
| Data-encryption CMK (per data class) | AWS KMS (CMK) | Annual auto-rotation enabled | Encrypts DynamoDB, S3 WORM; key policy least-privilege |
| Scoped-token signing key | Prod: KMS / AgentCore Identity (asymmetric); dev: HMAC | On suspicion + scheduled | Dev HMAC (`GATEWAY_TOKEN_SECRET`) is **not for production**; swap to KMS-held asymmetric |
| Approval-token signing key | Prod: KMS; dev: HMAC | On suspicion + scheduled | Same as above (`APPROVAL_TOKEN_SECRET`) |
| Cognito / JWT | Cognito-managed JWKS | AWS-managed | Verify via JWKS; never hardcode public keys |
| Connector credentials | AWS Secrets Manager | Per connector policy | Never in code/env files; least-privilege access; rotation lambdas |

### Principles
- No standing service accounts — every tool call uses a short-lived, single-use scoped token.
- Separate CMKs per data class enable data-class isolation and targeted revocation.
- Secret-zeroization on rotation; all key use is logged via CloudTrail (KMS data events).
- Token-signing-key compromise is **contained by rotation** (existing tokens expire in seconds and are single-use).
