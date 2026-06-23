# 08 — Public Safety / Public Health Case & Report
### Governed AI on AWS — part of the SLG Suite

> Transcribes and summarizes incidents, drafts reports from approved source material, and turns plain-language questions into validated surveillance queries — without establishing probable cause or making diagnoses.

**Problem.** Police, fire, EMS, emergency management and public health produce large amounts of narrative data, and surveillance questions often require SQL expertise.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).

## What it does
Classifies intent (summarize · report · surveillance), gathers from approved systems via the governed gateway, produces a **incident report draft**, runs a compliance check (grounding · accessibility · PII · domain guard), pauses at the **human review gate**, and finalizes only after approval.

**Guardrail.** AI must not independently establish probable cause, calculate dangerousness, recommend sentencing, make a medical diagnosis, or initiate enforcement. CJI, PHI and public data stay in separate environments; surveillance SQL is validated deterministically before execution.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/08-public-safety-health/` (Strands + Step Functions, `waitForTaskToken` gate). See `docs/`.

**Key systems:** Incident systems, governed data lake (Lake Formation), OpenSearch, KB. **Key obligations:** FBI CJIS v6.0, HIPAA/PHI, public-records.
