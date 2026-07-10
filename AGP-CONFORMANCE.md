# AGP v1.0 Conformance — SLG (State & Local Government)

**This pack conforms to the Aegis Governance Pattern (AGP) v1.0.** AGP is the governance *contract*
(8 controls, each fail-closed and negative-tested) that every suite implements once in its
`platform_core`, so agents inherit identity, authorization, audit, masking, approval, budget, and
grounding without re-deriving them. The canonical, versioned contract lives in the Aegis repo:
`docs/14-GOVERNANCE-PATTERN-VERSIONING.md`.

- **Contract version implemented:** AGP **1.0**
- **Implementation package:** `slg-agent-platform` (version declared in `MATURITY.yaml` / `pyproject.toml`)
- **Machine-readable claim:** `import slg_agent_platform; slg_agent_platform.AEGIS_GOVERNANCE_PATTERN_VERSION == "1.0"`

*Two versions are distinct: the **pattern** (AGP 1.0 — what a CISO reviews once) and this pack's
**implementation** (early 0.x). A reviewer approves the pattern once; each suite then shows it conforms.*

## The 8 required controls — implemented and proven here

| AGP v1.0 control | Implemented by | Proven by |
|---|---|---|
| 1. Identity (authN) — verified RS256/JWKS JWT; alg-confusion guarded; identity only from a verified claim | `jwt_verify.py` (RS256; `none`/HS rejected) | negative-demo #1–2 |
| 2. MCP / tool authorization gateway — deny-by-default; unregistered tool → deny | `mcp_gateway/gateway.py` + `policy.TOOL_REGISTRY` | negative-demo #4 |
| 3. Least-privilege intersection — effective = agent grant ∩ user entitlement | `mcp_gateway/policy.py` (`decide`) | negative-demo #3 |
| 4. Human approval (SoD, single-use) — consequential acts withheld in code; bound, single-use, approver ≠ requester | `mcp_gateway/approvals.py` (bound + NonceStore) | negative-demo #5–7 |
| 5. PII/PHI/regulated-data masking — fail-closed at every log/audit boundary (real-data mode requires NER; regex alone does not mask free-text names) | `pii.py` + `mcp_gateway/audit.py` | negative-demo #8 |
| 6. Audit (append-only + WORM) — every decision recorded; IAM deny on mutate; S3 Object Lock | `mcp_gateway/audit.py` + `audit_sinks.py` | negative-demo #9; clean-account run |
| 7. Token budgets — per-agent hard cap enforced before spend | `budget.py` | `platform_core/tests/test_budget.py`; negative-demo #10 |
| 8. Model gateway + grounding — brokered model access; grounding / output-schema checks; output guardrail **fails closed** (a configured guardrail that errors blocks + emits `guardrail_failclosed`) | `llm_factory.py` + `reasoning.py` + governance grounding | `make eval-311` |

Hero: Agent 01 (Resident Services / 311).

> Conformance is about the **control being present, fail-closed, and negative-tested** — not about
> production-readiness. See [`NOT-CLAIMS.md`](NOT-CLAIMS.md) for what this pack does not claim, and
> [`MATURITY.yaml`](MATURITY.yaml) for per-agent maturity and deployment evidence.
