# Runbook — Model Degradation Response (SLG Governed Agent Platform)
*Scope: detecting and responding to a drop in the quality, safety, or reliability of model-generated output — drift, a bad prompt/model change, or a provider-side regression. This is the **ongoing-monitoring** discipline a model-risk reviewer expects (NIST AI RMF MEASURE/MANAGE; SR 11-7-style posture for agencies that use it).*

## 1. What "degradation" looks like (signals)
| Signal | Source | Healthy baseline |
|---|---|---|
| **Grounding-failure rate** ↑ | `governance/grounding.py` results logged per run | low and stable |
| **HITL reject/edit rate** ↑ | human-gate decisions | stable; a spike means drafts got worse |
| **Guardrail block rate** ↑↓ | Bedrock Guardrails metrics | stable; a sudden change = prompt/model shift |
| **Eval regression** | `governance/evals/` golden-artifact harness in CI | 100% structural pass |
| **Accessibility failures** ↑ | `governance/accessibility/` | none |
| **Latency / error rate** ↑ | CloudWatch (per node) | within SLO |
| **Fairness drift** | `governance/fairness/` (flag/rank workflows) | within four-fifths |

Wire each to a CloudWatch alarm with a baseline threshold; alarm to the on-call channel.

## 2. Triage
1. **Did anything change?** Check the **prompt registry** (`governance/prompt_manifest.json`) and the model IDs (`llm_factory.py`) for a recent version bump. CI fails on un-bumped prompt drift, so an *un*-tracked change implies an out-of-band edit — treat as a change-control incident.
2. **Is it safety or quality?** Guardrail-block changes → safety; grounding/HITL-reject changes → quality.
3. **Is it provider-side?** If no prompt/model change on your side, suspect a Bedrock model revision — confirm against the eval harness on a fixed corpus.

## 3. Response (in order of preference)
1. **Roll back the prompt/model version.** The prompt registry pins each prompt by hash and the LLM factory pins model IDs — revert to the last known-good version (a config/IaC change, no code rewrite). Re-run the eval harness to confirm recovery.
2. **Raise the human-review ratio.** Lower the auto-route threshold so more drafts go to a human while you investigate — the HITL gate is the safety net by design.
3. **Fail to a safer tier / deterministic path.** Route the affected step to a more conservative model (or, where one exists, the deterministic service) until resolved. Guardrails stay mandatory.
4. **Pause the agent** (Step Functions disabled) if safety is implicated and the above don't restore baseline — better a paused agent than a degraded one acting in a regulated workflow.

## 4. Recovery & verification
- Re-run `python -m governance.evals.run_evals` and the agent test suite; confirm grounding/eval baselines restored.
- Confirm HITL reject rate and guardrail metrics return to baseline over a monitoring window.
- Only then restore the auto-route threshold / re-enable the agent.

## 5. Prevent recurrence
- Add the failing case to the **eval harness** and, if safety-related, the **red-team** set (`governance/redteam/`) so CI catches it next time.
- Keep eval baselines under version control; treat a model/prompt change as a model-risk change-control event with documented before/after eval results.
- **Stand up the eval/grounding harness before deploying a new agent** — retrofitting evaluation is harder than building on it.
