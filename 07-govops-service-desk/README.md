# 07 — GovOps IT Service Desk & Modernization
### Governed AI on AWS — part of the SLG Suite

> Answers IT questions, diagnoses common incidents, creates and routes tickets, and proposes remediation — while destructive operations require an SRE's approval.

**Problem.** SLG IT faces aging systems, workforce shortages, large help-desk volumes and incomplete documentation. Tier-1 load and legacy knowledge gaps slow everything.

**Maturity:** Demonstrated + Deployable-by-design. Runs end-to-end with **no API key** (`EXTRACT_MODE=demo`).

## What it does
Classifies intent (support · incident · runbook · status), gathers from approved systems via the governed gateway, produces a **diagnosis and proposed action**, runs a compliance check (grounding · accessibility · PII · domain guard), pauses at the **human review gate**, and finalizes only after approval.

**Guardrail.** The agent must not independently disable accounts, alter firewall rules, delete infrastructure, or remediate production systems without policy checks and approval; runbook execution requires an SRE-entitled approver (itsm.run_runbook is high-risk).

## Run the demo
```bash
pip install -e ../platform_core && pip install langgraph streamlit
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```

## Architecture
LangGraph `StateGraph` with `interrupt_before=["human_review_gate"]` (`agent/graph.py`); a framework-free runner (`agent/core.py`) honors the same HITL contract for testing. Every system touch flows through the deny-by-default MCP gateway (agent grant ∩ user entitlement). AWS-native rebuild: `../aws-native-reference/07-govops-service-desk/` (Strands + Step Functions, `waitForTaskToken` gate). See `docs/`.

**Key systems:** ITSM (ServiceNow), Systems Manager, Security Hub/GuardDuty, KB. **Key obligations:** change control, least-privilege ops, audit.
