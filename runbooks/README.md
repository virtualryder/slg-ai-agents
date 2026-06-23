# Operational Runbooks

## Deployment runbooks (architect, real AWS account)
- **Platform:** `WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` — 16-stage end-to-end deploy of the governed foundation + Whole-of-Government orchestration (networking, KMS, Cognito, Bedrock + Guardrails, knowledge base, gateway, agents, WoG saga, HITL, audit/WORM, accessibility, smoke tests, go-live).
- **Per agent:** each agent ships `<agent>/docs/DEPLOY-RUNBOOK.md` — the agent-specific path (role mapping, its connectors, deploy command, Guardrail specifics, HITL wiring, smoke tests, go-live checklist):
  - `01-resident-services-311/docs/DEPLOY-RUNBOOK.md` … `08-public-safety-health/docs/DEPLOY-RUNBOOK.md`
- **WoG saga (AWS-native):** `aws-native-reference/wog-platform/DEPLOY.md`.

## Operational runbooks
- `HITL-QUEUE-OPERATIONS.md` — running the human-approval queue (the control that makes a writing agent safe).
- `INCIDENT-RESPONSE.md` · `DR-RUNBOOK.md` · `MODEL-DEGRADATION-RESPONSE.md` — port/tailor from HCLS for SLG data classes (CJI/FTI/PHI separation). *(Stubs — prioritize per engagement.)*
