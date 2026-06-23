# 06 — Procurement, Contracting & Grants
### Governed AI on AWS — part of the SLG Suite

> Finds contract vehicles and funding, drafts solicitation sections, and organizes bid evidence against published criteria — while the award decision stays with a procurement officer.

**Problem.** Public procurement is document-intensive and slow: develop requirements, draft solicitations, answer vendor questions, review submissions, document decisions.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).
> **Withheld in code:** `procurement.award` (award) is **not** in this agent's grants — a human role holds it (verified by test).

## Intent → action → outcome
- **find** → `FIND_VEHICLES` (read) → VEHICLES_FOUND
- **draft_rfp** → `DRAFT_RFP` (write · HITL) → RFP_DRAFTED
- **compare** → `COMPARE_BIDS` (read) → BIDS_COMPARED
- **status** → `STATUS_LOOKUP` (read) → STATUS_PROVIDED

**Guardrail.** The agent organizes evidence and applies a deterministic, published scoring rubric; it must NOT select a winning bidder or alter evaluation criteria — the procurement officer owns the legally consequential award.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/06-procurement-grants/`. See `docs/`.

**Key systems:** ERP/e-procurement, grants systems, IDP, KB. **Key obligations:** procurement law, required clauses, grant terms, immutable evaluation record.
