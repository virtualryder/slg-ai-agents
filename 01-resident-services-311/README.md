# 01 — Resident Services & 311 Navigator
### Governed AI on AWS · the reference agent for the SLG Suite

> Residents must navigate hundreds of agency pages, phone numbers, PDFs, forms, and
> departmental boundaries — often without knowing which agency owns their problem.
> This agent understands a plain-language request, determines the responsible
> agency, retrieves authoritative public content, drafts a **cited** answer, and —
> only for an authenticated, consented resident — checks status, opens a 311
> request, or books an appointment. Every consequential write passes a
> framework-enforced human-approval gate.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API
key** (`EXTRACT_MODE=demo`, deterministic fixtures). Production-readiness (IdP
integration, live 311/CRM + KB connectors, accessibility audit, ATO) is the
engagement.

## What it does
1. Classifies intent (service_request · status_lookup · appointment · policy_question · escalate).
2. Retrieves approved public content via the gateway (`kb.search_policy`).
3. Requires **identity verification** before any personal/account disclosure — a name + address is never enough.
4. Drafts a grounded answer with **source citations** for every fact.
5. Runs a compliance check: grounding (no fabricated fees/dates/agencies), WCAG/plain-language, PII.
6. Pauses at the **human review gate**; a city reviewer approves before any write.
7. Finalizes: opens a 311 request, books an appointment, answers, or escalates.

## Run the demo (no API key)
```bash
pip install -e ../platform_core && pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py          # CLI walk-through of 4 scenarios
streamlit run app.py             # dashboard at http://localhost:8501
```

## Test
```bash
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
- **Workflow:** LangGraph `StateGraph`, `interrupt_before=["human_review_gate"]` (see `agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing.
- **Tool access:** every system touch flows through the deny-by-default MCP gateway (`platform_core/slg_agent_platform/mcp_gateway`) — agent grant ∩ user entitlement, scoped tokens, PII-masked append-only audit.
- **AWS-native rebuild:** `../aws-native-reference/01-resident-services-311/` (Strands + Step Functions with a `waitForTaskToken` human gate).
- **Container:** `agent/serve.py` implements the AgentCore Runtime `/invocations` + `/ping` contract; `Dockerfile` is ARM64.

See `docs/` for the AWS deployment guide, integration guide, compliance mapping, and ROI analysis.
