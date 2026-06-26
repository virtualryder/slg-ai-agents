# Golden Path 311 — Customer Evidence Package

Evidence an AWS Solutions Architect can hand to a customer's security review board for the **one fully-wired agent** (Resident Services / 311). This package is reproducible — every artifact below can be regenerated with the listed command.

## Contents
| File | What it gives the reviewer |
|---|---|
| `ARCHITECTURE-AND-BOM.md` | Architecture diagram, AWS bill of materials, and the IAM least-privilege matrix |
| `CONTROL-EVIDENCE.md` | Control statements (→ NIST matrix), test & scan evidence with commands, accessibility |
| `COST-AND-LIMITATIONS.md` | Pilot cost estimate, known limitations, and the shared-responsibility split |

## Reproduce the evidence (commands)
```bash
# Unit tests (control plane + governance) — no API key
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance/tests -q

# IaC lint (golden path + all templates)
cfn-lint --ignore-checks E3006 infra/cloudformation/*.yaml infra/golden-path-311/template.yaml

# Python security
bandit -r platform_core governance aws-native-reference -lll
pip-audit

# Deploy + smoke test the golden path (in the customer/SA account)
cd infra/golden-path-311 && ./deploy.sh && ./smoke_test.sh && ./destroy.sh
```

CI runs the same gates on every PR: `.github/workflows/ci.yml`. Full control mapping: `docs/NIST-800-53-CONTROL-MATRIX.md`. Threat model: `docs/THREAT-MODEL.md`.
