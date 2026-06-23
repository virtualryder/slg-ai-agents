# 04 — Benefits / HHS Caseworker Assist
### Governed AI on AWS — part of the SLG Suite

> Prescreens (nonbinding), assembles evidence, identifies missing documents, and drafts notices — while the deterministic eligibility engine and a human supervisor own the determination.

**Problem.** Medicaid, SNAP, TANF, UI and childcare involve complex rules and heavy documentation. Caseworkers move across systems while residents re-supply similar information.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).
> **Withheld in code:** `eligibility.adjudicate` (adjudicate) is **not** in this agent's grants — a human role holds it (verified by test).

## Intent → action → outcome
- **prescreen** → `PRESCREEN` (read) → PRESCREENED
- **status** → `STATUS_LOOKUP` (read) → STATUS_PROVIDED
- **apply** → `CREATE_APPLICATION` (write · HITL) → APPLICATION_CREATED
- **notice** → `DRAFT_NOTICE` (write · HITL) → NOTICE_DRAFTED

**Guardrail.** Eligibility determination runs in a deterministic rules engine OUTSIDE the LLM. The agent prescreens (nonbinding), organizes evidence and drafts notices; it never adjudicates, denies, or terminates a benefit.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/04-benefits-caseworker/`. See `docs/`.

**Key systems:** Integrated eligibility system, IDP, Identity, KB. **Key obligations:** HIPAA / MARS-E→ARC-AMPE, IRS Pub 1075, SSA data-exchange, program rules.
