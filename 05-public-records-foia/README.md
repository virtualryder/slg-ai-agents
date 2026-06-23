# 05 — Public Records / FOIA & Redaction
### Governed AI on AWS — part of the SLG Suite

> Searches, classifies responsiveness, proposes redactions and assembles the production package with an index — while public release stays with a records officer.

**Problem.** Counties hold deeds, court records, emails, video and scanned paper. Staff must find responsive records, dedupe, detect exemptions, redact, and meet a statutory clock.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).
> **Withheld in code:** `records.release` (release) is **not** in this agent's grants — a human role holds it (verified by test).

## Intent → action → outcome
- **search** → `SEARCH` (read) → SEARCH_COMPLETE
- **classify** → `CLASSIFY` (read) → CLASSIFIED
- **redact** → `PROPOSE_REDACTION` (read) → REDACTIONS_PROPOSED
- **package** → `ASSEMBLE_PACKAGE` (write · HITL) → PACKAGE_READY
- **status** → `STATUS_LOOKUP` (read) → STATUS_PROVIDED

**Guardrail.** The agent PROPOSES redactions and flags exemptions; it never applies a final redaction or releases records — a records officer reviews and releases. Prompts and AI traces may themselves be records subject to retention.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/05-public-records-foia/`. See `docs/`.

**Key systems:** Records/ECMS, OpenSearch, KB. **Key obligations:** state public-records law, retention/legal-hold, personal-privacy exemptions.
