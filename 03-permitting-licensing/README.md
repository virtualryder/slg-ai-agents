# 03 — Permitting & Licensing
### Governed AI on AWS — part of the SLG Suite

> Identifies the right permit, explains requirements in plain language, checks parcel/zoning, prefills and routes the package — while issuance stays with an authorized official.

**Problem.** Building permits and licenses cross several departments (zoning, planning, fire, engineering). Applicants cannot tell what is missing or which agency is holding the case.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).\n> **Withheld in code:** `permitting.issue_permit` (issue permit) is **not** in this agent's grants — a human role holds it (verified by test).

## What it does
Classifies intent (requirements · status · apply · route), gathers from approved systems via the governed gateway, produces a **permit application package**, runs a compliance check (grounding · accessibility · PII · domain guard), pauses at the **human review gate**, and finalizes only after approval.

**Guardrail.** The agent may recommend an application is complete, but permit issuance and code interpretation remain with an authorized official; it must distinguish a deterministic code rule from a discretionary judgment.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/03-permitting-licensing/` (Strands + Step Functions, `waitForTaskToken` gate). See `docs/`.

**Key systems:** Permitting (Accela/Tyler), GIS, IDP, KB. **Key obligations:** local code, ADA Title II, records retention.
