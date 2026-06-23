# GovOps IT Service Desk & Modernization — AWS Deployment Runbook
*Audience: AWS Solutions Architect / customer engineer. Outcome: Agent 07 (07-govops-service-desk) running in a real AWS account, commercial or GovCloud. Companion to the platform runbook `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md` (shared foundation) — this file is the agent-specific path.*

> **Prove it locally first (no AWS spend):**
> ```bash
> pip install -e ../platform_core && pip install langgraph
> EXTRACT_MODE=demo python demo/demo_run.py
> PYTHONPATH=../platform_core:..:. python -m pytest tests -q
> ```

## What this agent touches
- **Acting role (IdP claim `custom:slg_role`):** `IT_ANALYST`
- **Granted tools (gateway targets):** `itsm.get_ticket`, `itsm.create_ticket`, `itsm.run_runbook (SRE only)`, `kb.search_policy`
- **Systems of record / connectors:** ITSM (ServiceNow) · Systems Manager · Security Hub/GuardDuty · KB
- **Consequential action withheld in code:** none beyond the human-approval gate on every write.

## Stage A — Shared foundation (once per account)
Complete Stages 1–7 of `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`: Org/landing zone + data-class isolation, networking (VPC + Bedrock VPC endpoint + WAF), **KMS CMK**, **Cognito** federated to your IdP, **Bedrock model access + Guardrail**, **Knowledge Base** over approved content, and the **MCP gateway** path (portable for any region incl. GovCloud, or AgentCore).

## Stage B — Map the role
In Cognito, map the agency IdP group for this workflow to `custom:slg_role = IT_ANALYST`. The gateway authorizes `agent grant ∩ user entitlement`, so only users with this role can drive the agent — and only for this agent's granted tools.

## Stage C — Implement / point the connectors
For each system above, implement the agency adapter in `platform_core/slg_agent_platform/connectors/live.py`, or set `<KIND>_BASE_URL` for the bundled REST adapter (e.g. `ITSM_BASE_URL`). Method signatures match the fixtures — no agent code changes demo→live. Validate each connector against the live system before go-live.

## Stage D — Package & deploy
```bash
export CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket
scripts/build_lambdas.sh 07-govops-service-desk
aws s3 cp .build/07-govops-service-desk-lambdas.zip s3://$CODE_BUCKET/
aws s3 sync infra/cloudformation s3://$CFN_BUCKET/slg --exclude "README.md"

# native (Step Functions + Lambda, waitForTaskToken HITL) — or swap 'native' for 'container'
scripts/deploy.sh 07-govops-service-desk dev portable native
#                 ^AgentId  ^env ^GatewayMode ^DeployMode   (use 'portable' in GovCloud)
```
This nests the security (KMS, **Guardrail**, Cognito, least-privilege role), data (append-only DynamoDB audit, **S3 Object Lock WORM**, HITL table), gateway, and agent stacks for `AgentId=07-govops-service-desk`.

## Stage E — Guardrail specifics for this agent
Confirm the Bedrock Guardrail attached to this agent blocks/masks PII (SSN/bank/card BLOCK; driver-ID/email/phone ANONYMIZE), denies out-of-scope determinations, and runs **contextual grounding checks** on drafting. Set `BEDROCK_GUARDRAIL_ID` and `ENVIRONMENT=production` (the LLM factory refuses to start without a guardrail in production).

## Stage F — Wire the human-in-the-loop gate
The `human_review_gate` runs as Step Functions `waitForTaskToken`: the execution pauses and notifies a reviewer (SNS/SES or your console) with the draft + token; the reviewer approves and your app calls `SendTaskSuccess`. Operate per `runbooks/HITL-QUEUE-OPERATIONS.md`.

## Stage G — Smoke tests (must pass before go-live)
```bash
# 1. Read path: invoke the agent with a benign request and confirm a grounded, cited answer
#    e.g. "My VPN is down"
# 2. Write path: drive an action that calls itsm.create_ticket; confirm it PAUSES at the gate,
#    then approve and confirm the write commits and lands in the audit table.
# 3. Authorization: call a tool this role is NOT entitled to -> expect DENY in the audit table.
# 4. Accessibility: run governance/accessibility checks on a generated response.
```

## Stage H — Go-live checklist
- [ ] `IT_ANALYST` mapping verified end-to-end via the IdP
- [ ] All connectors validated against live systems
- [ ] Guardrail attached and mandatory (`ENVIRONMENT=production`)
- [ ] Audit append-only (SCP denies Update/Delete) + WORM retention set to records schedule
- [ ] HITL queue operational; approver-identity enforcement tested
- [ ] Smoke tests Stage G green; accessibility audit passed
- [ ] DR / incident / model-degradation runbooks reviewed (`runbooks/`)

## AWS-native variant
`aws-native-reference/07-govops-service-desk/` is the Strands + Step Functions rebuild (deterministic core + 5 Lambdas + `*.asl.json` with a `waitForTaskToken` gate); see its `DEPLOY.md`.
