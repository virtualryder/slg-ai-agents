# Governance & Evaluation Framework
Built in from the first commit. All run with **no API key**.

| Control | File | What it enforces |
|---|---|---|
| Grounding verification | `grounding.py` | No fabricated fee/date/agency reaches a resident |
| Prompt registry | `prompt_registry.py` + `prompt_manifest.json` | Hash-pinned prompts; CI fails on un-bumped drift |
| Eval harness | `evals/run_evals.py` | Golden-artifact structural regression |
| Red team | `redteam/scenarios.py` | Injection, PII/CJI/FTI exfiltration, authz bypass |
| Fairness | `fairness/disparate_impact.py` | EEOC four-fifths rule for flag/rank workflows |
| Accessibility | `accessibility/wcag.py` | ADA Title II / WCAG 2.1 AA on generated output |
| Control mappings | `controls/control_mappings.py` | Regime → platform control → AWS service |
| HITL enforced | `tests/test_hitl_enforced.py` | High-risk tools cannot execute without approval |

Run: `PYTHONPATH=../platform_core:.. python -m pytest governance -q`
