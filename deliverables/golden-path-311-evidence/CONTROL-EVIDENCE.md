# Golden Path 311 — Control Statements, Test & Scan Evidence

## Control statements (summary; full matrix: `docs/NIST-800-53-CONTROL-MATRIX.md`)
| Concern | Control statement | Evidence (test / file) |
|---|---|---|
| Autonomous consequential action | Consequential actions are withheld from agent grants; high-risk requires a bound, single-use, SoD human approval | `test_consequential_actions_withheld_from_agents`, `approvals.py`, `test_mcp_gateway.py` |
| Identity / impersonation | RS256/JWKS verification (iss/aud/exp + alg guard); roles only from a verified token | `jwt_verify.py`, `test_jwt_verify.py` |
| Least privilege | Deny-by-default intersection (agent grant ∩ user entitlement); per-function IAM; Bedrock scoped to model+guardrail ARNs | `policy.py`, `template.yaml`, `security.yaml` |
| Audit integrity | Append-only (conditional write + IAM Update/Delete deny); WORM by data class | `audit_sinks.py`, `test_audit_append_only.py`, `data.yaml` |
| Data leakage | Fail-closed PII/CJI/FTI masking; Guardrails in/out; private-connectivity inference (Bedrock via PrivateLink) | `pii.py`, `test_pii.py`, `security.yaml` |

## Test evidence (reproducible)
```bash
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance/tests -q
```
Result (last run, this environment, 2026-06-26): **69 passed** — including the negative-case tests proving self-approval, replay, args-tampering, wrong-tool, and expired approvals are rejected; forged/expired/wrong-issuer JWTs are rejected; and ML-masking failures redact rather than leak.

## Static analysis / IaC evidence (reproducible)
| Gate | Command | Last result |
|---|---|---|
| IaC lint | `cfn-lint --ignore-checks E3006 infra/cloudformation/*.yaml infra/golden-path-311/template.yaml` | clean |
| Python SAST | `bandit -r platform_core governance aws-native-reference -lll` | **0 High** |
| Dependency audit | `pip-audit` | advisory (CI) |
| IaC security | `checkov -d infra --soft-fail` | advisory (CI) |
| Secret scan | TruffleHog (CI, verified-only) | n/a |
| SBOM | `cyclonedx-py environment` (CI artifact) | `sbom-cyclonedx` |

CI enforces these on every PR: `.github/workflows/ci.yml`.

## Accessibility (ADA Title II / WCAG 2.1 AA)
Accessibility of AI output is checked in the governance suite (`governance/accessibility/`); production front-ends must additionally run **axe-core** (automated) plus manual assistive-technology testing. Title II deadlines: **Apr 26 2027** (≥50k population) / **Apr 26 2028** (smaller + special districts). Owner: customer; method documented in `docs/COMPLIANCE-CONTROL-MAPPINGS.md`.
