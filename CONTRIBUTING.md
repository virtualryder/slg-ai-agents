# Contributing

Thanks for helping improve the SLG AI Agent accelerator. This is a governed reference for regulated public-sector AI on AWS, so changes are held to a security-and-evidence bar.

## Dev setup
```bash
pip install -e platform_core
pip install pytest cfn-lint bandit
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance/tests -q   # no API key needed
```

## Ground rules
- **No consequential action may be added to an agent's tool grants.** Issue-permit / adjudicate / release-records / award stay withheld; a test enforces this (`test_consequential_actions_withheld_from_agents`).
- **Fail closed.** New control-plane code must reject on error/ambiguity, never default-allow. Add the negative-case test alongside the feature.
- **No secrets in code or fixtures.** No real PII/CJI/FTI in tests; use synthetic data.
- **Every figure in customer-facing docs/decks must be cited** in `decks/DECK-SOURCES.md` with an evidence tier.

## Definition of done (PR checklist)
- [ ] Unit tests added/updated; `pytest` green with no API key.
- [ ] `cfn-lint` clean on any changed CloudFormation/SAM (US partition).
- [ ] `bandit` shows no new High findings on changed Python.
- [ ] Docs updated (README / relevant `docs/*`), and `CHANGELOG.md` has an entry.
- [ ] If a control changed, `docs/NIST-800-53-CONTROL-MATRIX.md` evidence column updated.
- [ ] No overclaiming language (see `docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` P0).

## Commit / branch
Small, reviewable commits; conventional prefixes (`feat:`, `fix:`, `docs:`, `sec:`, `infra:`). Branch from `main`.

## Security-sensitive changes
Changes to `mcp_gateway/`, `jwt_verify.py`, `pii.py`, IAM, or audit require an updated threat-model note and a reviewer ack. Report vulnerabilities per `SECURITY.md` (do not open a public issue).
