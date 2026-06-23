# 02 — Forms & Intelligent Document Processing
### Governed AI on AWS — part of the SLG Suite

> Determines the right form, extracts and validates fields, and assembles a completed official form — collecting only what the applicant supplies, never inventing legally significant facts.

**Problem.** Government still runs on forms. The same resident repeatedly submits information the government already holds; staff re-key it, hunt for missing fields, and classify attachments.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).

## Intent → action → outcome
- **extract** → `EXTRACT` (read) → EXTRACTED
- **validate** → `VALIDATE` (read) → VALIDATED
- **assemble** → `ASSEMBLE` (write · HITL) → ASSEMBLED
- **status** → `STATUS_LOOKUP` (read) → STATUS_PROVIDED

**Guardrail.** The agent must not infer or fabricate a legally significant fact (income, identity, dates) the applicant did not supply — it may only identify a missing item.

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/02-forms-idp/`. See `docs/`.

**Key systems:** IDP (Bedrock Data Automation / Textract), KB, Identity, Consent, 311/CRM. **Key obligations:** IRS Pub 1075 (FTI), HIPAA, DPPA, state privacy.
