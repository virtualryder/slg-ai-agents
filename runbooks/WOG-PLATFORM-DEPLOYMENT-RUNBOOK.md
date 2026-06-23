# Whole-of-Government Platform — AWS Deployment Runbook
*Audience: AWS Solutions Architect / customer cloud engineer. Outcome: the governed SLG agent platform + the Whole-of-Government orchestration layer running in a customer account, commercial or GovCloud. This is a GTM **deploy asset** — pair it with `gtm/WOG-PLATFORM-GTM-STORY.md` and the decks.*

> **What you will have at the end:** a deny-by-default MCP gateway, Bedrock + Guardrails, a knowledge base, at least one specialist agent, the WoG saga (Step Functions + Lambdas backed by DynamoDB + EventBridge), tamper-evident audit + WORM retention, and a working human-approval gate — verified with smoke tests.

> **Golden rule:** prove it locally first (no AWS spend), then deploy. Every stage below has a local check.

---

## Stage 0 — Decisions (make these before touching the console)
| Decision | Options | Default | Drives |
|---|---|---|---|
| Region posture | commercial \| GovCloud (US) | commercial, GovCloud-ready | `DeploymentResidency`, gateway path |
| Gateway path | `portable` (API GW + Cognito + STS) \| `agentcore` (Bedrock AgentCore Gateway) | `portable` | which gateway stack; **GovCloud must use `portable`** |
| Agent runtime | `native` (Step Functions + Lambda) \| `container` (ECS/AgentCore Runtime) | `native` | `DeployMode` |
| Data classes in scope | CJI · FTI · PHI · EDU · PII · PUBLIC | per workload | account/VPC isolation |
| First workload | one agent (e.g. 01) and/or one life-event (e.g. moving) | 01 + moving | pilot scope |

**GovCloud note (verified 2026):** Bedrock + Guardrails + Knowledge Bases are FedRAMP High / IL-4/5 in GovCloud; AgentCore is in GovCloud (US-West) but Memory / Gateway semantic search / Policy / Registry are not yet — so set `GatewayMode=portable` there.

---

## Stage 1 — Prerequisites
- **Org & landing zone:** AWS Organizations + Control Tower. Separate accounts for *security/logging*, *shared agent services*, and **one boundary per regulated data class** (CJI, FTI, PHI, EDU, public) — do **not** pool government data classes in one boundary.
- **Access:** an admin/deployment role in the target account; `aws` CLI v2 configured; `git`, `python3.12`, `docker` (only for container mode).
- **IdP:** the agency identity provider (SAML 2.0 / OIDC) ready to federate into Amazon Cognito / IAM Identity Center, with a group/claim that maps to `custom:slg_role` (e.g. `RESIDENT_SERVICES_AGENT`, `ELIGIBILITY_CASEWORKER`).
- **Bedrock model access:** request access to the Claude models in the target Region (Console → Bedrock → Model access).
- **Knowledge content:** the approved public/policy documents you will ground answers in (PDFs, web exports), in an S3 bucket.
- **Buckets:** a CloudFormation staging bucket (`CFN_BUCKET`) and a code bucket (`CODE_BUCKET`).

**Local check (no AWS):**
```bash
git clone <repo> && cd slg-ai-agents
pip install -e platform_core && pip install pytest langgraph
PYTHONPATH=platform_core:. python -m pytest platform_core/tests governance gov_platform/wog_orchestration/tests -q   # expect green
PYTHONPATH=platform_core:. python aws-native-reference/wog-platform/local_runner.py                                   # 5 life-events run
```

---

## Stage 2 — Networking (per workload account)
Deploy the network stack (VPC, private subnets, NAT, security groups, **Bedrock VPC interface endpoint** so inference never traverses the public internet):
```bash
aws cloudformation deploy --template-file infra/cloudformation/network.yaml \
  --stack-name slg-net-dev --parameter-overrides Environment=dev
```
No public inbound; all inter-service traffic stays in the VPC. Front public entry points with **CloudFront + AWS WAF**.

---

## Stage 3 — Security foundation (KMS, Cognito, IAM)
Deploy the security stack — **KMS CMK** (per environment, key rotation on), **Cognito User Pool + app client** (federate your IdP; add the `custom:slg_role` attribute), and the **least-privilege agent role**:
```bash
aws cloudformation deploy --template-file infra/cloudformation/security.yaml \
  --stack-name slg-sec-dev --parameter-overrides AgentId=01-resident-services-311 Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM
KMS_ARN=$(aws cloudformation describe-stacks --stack-name slg-sec-dev \
  --query "Stacks[0].Outputs[?OutputKey=='KmsKeyArn'].OutputValue" --output text)
```
Map your IdP groups → `custom:slg_role`. This claim is what the gateway authorizes against (`agent grant ∩ user entitlement`).

---

## Stage 4 — Bedrock Guardrails (the safety control)
The `security.yaml` stack provisions a **Bedrock Guardrail** with PII filters (SSN/bank/card BLOCK; driver-ID/email/phone ANONYMIZE), a prompt-attack filter, and a denied-topic for unauthorized determinations. Capture its ID and version, and require it in production:
```bash
GUARDRAIL_ID=$(aws cloudformation describe-stacks --stack-name slg-sec-dev \
  --query "Stacks[0].Outputs[?OutputKey=='GuardrailId'].OutputValue" --output text)
# agents read these:
export BEDROCK_GUARDRAIL_ID=$GUARDRAIL_ID BEDROCK_GUARDRAIL_VERSION=DRAFT ENVIRONMENT=production
```
Add **contextual grounding checks** in the guardrail config for drafting flows. (The LLM factory refuses to start in `ENVIRONMENT=production` without a guardrail — fail-closed.)

---

## Stage 5 — Knowledge base (grounded retrieval)
Create an **Amazon Bedrock Knowledge Base** over your approved-content S3 bucket (vector store: OpenSearch Serverless or Aurora pgvector). Sync it. This is the substrate the resident-services and policy answers ground against, with source citations. (For an enterprise search experience over many repositories with ACL trimming, **Amazon Q Business** is the alternative — use source-level access-control propagation.)

---

## Stage 6 — Data stores: audit + WORM (tamper-evident)
Deploy the data stack — **append-only DynamoDB audit** (PITR on; an SCP denies `dynamodb:UpdateItem`/`DeleteItem` on the audit partition), the **HITL queue table**, and the **S3 Object Lock (COMPLIANCE/WORM)** bucket for finalized snapshots:
```bash
aws cloudformation deploy --template-file infra/cloudformation/data.yaml \
  --stack-name slg-data-dev --parameter-overrides AgentId=01-resident-services-311 Environment=dev KmsKeyArn=$KMS_ARN
```
Tune the WORM retention period to the customer's records-retention schedule (default 7 yr; FTI/PHI floor 6 yr).

---

## Stage 7 — The MCP authorization gateway
**Portable path (any region incl. GovCloud):** API Gateway HTTP API + Cognito JWT authorizer in front of the connector Lambdas.
```bash
# staged by quickstart in Stage 9; or deploy gateway-portable.yaml standalone
```
**AgentCore path (AgentCore regions):** register each connector Lambda as an **AgentCore Gateway target** (`agentcore-gateway.yaml`); tool names map 1:1 to `policy.TOOL_REGISTRY` (`<kind>.<method>`). Inbound auth via **AgentCore Identity** (Cognito/OIDC), outbound via the gateway role. Migrating portable→agentcore later changes only this stack.

**Connectors:** implement each agency adapter in `platform_core/slg_agent_platform/connectors/live.py`, or set `<KIND>_BASE_URL` (e.g. `PERMITTING_BASE_URL`) to use the bundled REST adapter. Method signatures match the fixtures, so **no agent code changes** demo→live.

---

## Stage 8 — Package the code
```bash
export CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket
scripts/build_lambdas.sh 01-resident-services-311      # vendors platform_core + governance
scripts/build_lambdas.sh wog-platform                  # vendors platform_core + gov_platform + governance
aws s3 cp .build/01-resident-services-311-lambdas.zip s3://$CODE_BUCKET/
aws s3 cp .build/wog-platform-lambdas.zip            s3://$CODE_BUCKET/wog-platform-lambdas.zip
aws s3 sync infra/cloudformation s3://$CFN_BUCKET/slg --exclude "README.md"
```

---

## Stage 9 — Deploy a specialist agent (Agent 01 reference)
One master stack provisions a customer-isolated agent (nests security/data/gateway/agent):
```bash
scripts/deploy.sh 01-resident-services-311 dev portable native
#                 ^AgentId                  ^env ^GatewayMode ^DeployMode
```
This yields: the agent (native = Step Functions + Lambda with a `waitForTaskToken` HITL gate, or container = ECS/AgentCore Runtime), wired to the gateway, Guardrail, audit, and WORM. Repeat per agent (`02-forms-idp` … `08-public-safety-health`) — each declares its granted tools and the consequential action it is *forbidden* to call.

**Local check before deploy:**
```bash
PYTHONPATH=platform_core:.:01-resident-services-311 python -m pytest 01-resident-services-311/tests -q
EXTRACT_MODE=demo python 01-resident-services-311/demo/demo_run.py
```

---

## Stage 10 — Deploy the Whole-of-Government platform (live)
This is the orchestration layer: **EventBridge** compliance bus, **DynamoDB** consent + event + idempotency tables (KMS-encrypted), **S3 Object Lock** evidence bucket, the three saga **Lambdas** (gate/step/compensate, `WOG_BACKEND=aws`), a least-privilege Lambda role, and the **Step Functions** saga:
```bash
aws cloudformation deploy --template-file infra/cloudformation/wog-platform.yaml \
  --stack-name slg-wog-dev \
  --parameter-overrides Environment=dev KmsKeyArn=$KMS_ARN \
                        CodeBucket=$CODE_BUCKET CodeKey=wog-platform-lambdas.zip \
                        DeploymentResidency=us \
  --capabilities CAPABILITY_NAMED_IAM
SAGA_ARN=$(aws cloudformation describe-stacks --stack-name slg-wog-dev \
  --query "Stacks[0].Outputs[?OutputKey=='SagaArn'].OutputValue" --output text)
```
At cold start each Lambda runs `_shared.bootstrap()` → with `WOG_BACKEND=aws` it wires `AwsConsentStore` (DynamoDB), `AwsComplianceEventBus` (DynamoDB + EventBridge), `AwsIdempotencyStore` (DynamoDB conditional put = exactly-once). Handler code is identical to local.

---

## Stage 11 — Wire the human-in-the-loop queue
The `Gate` state runs as `waitForTaskToken` in production: the execution **pauses** and a notification (SNS/SES, or a reviewer console) is sent with the draft + task token. The reviewer/resident approves; your app calls `SendTaskSuccess` with the approval payload to resume. Operate this per `runbooks/HITL-QUEUE-OPERATIONS.md` (SLAs, queue-depth alarms, approver-identity enforcement).

---

## Stage 12 — Observability & audit correlation
- **CloudWatch:** dashboards/alarms for HITL queue depth, approval latency, error rate, saga failures, Bedrock throttling.
- **CloudTrail:** all API calls; correlate with the gateway audit + compliance events into one case-level record (partition by `correlation_id`).
- **EventBridge rules:** route compliance events to the audit sink and to any SIEM.

---

## Stage 13 — Accessibility validation (ADA Title II)
Run the deterministic WCAG checks (`governance/accessibility/`) in CI on generated output, and add **axe-core** for full automated auditing plus a manual screen-reader pass before go-live. AI-generated interfaces, documents, captions, and messages are in scope (deadlines Apr 2027 / Apr 2028).

---

## Stage 14 — Verification & smoke tests (must pass before go-live)
```bash
# 1. Start a WoG life-event execution (moving) and watch it complete
aws stepfunctions start-execution --state-machine-arn $SAGA_ARN --input file://execution-input.json
# 2. Force a failure (point a step at a down connector) and confirm COMPENSATED in the event store
# 3. Human-gate test: start an execution, confirm it PAUSES, approve via SendTaskSuccess, confirm it finalizes
# 4. Authorization test: call a tool the acting role is not entitled to -> expect DENY in the audit table
# 5. Withheld-action test: confirm no agent can invoke issue_permit / adjudicate / release / award
# 6. Evidence test: assemble the case-level evidence package; confirm retention = max data-class floor
```
Local equivalents (run anytime, no AWS): `pytest` (179 tests) + `local_runner.py` (saga + compensation + pause).

---

## Stage 15 — Go-live checklist
- [ ] Bedrock model access approved; **Guardrail attached and mandatory** (`ENVIRONMENT=production`)
- [ ] IdP federated; `custom:slg_role` mapping verified for every role in scope
- [ ] Data classes isolated by account/VPC boundary (CJI/FTI/PHI/EDU/public)
- [ ] Audit table append-only (SCP denies Update/Delete); PITR on; WORM retention set to records schedule
- [ ] KMS CMK per environment; key policy restricts to the agent/lambda roles
- [ ] Connectors validated against live systems (or `<KIND>_BASE_URL` set)
- [ ] HITL queue operational; approver-identity enforcement tested
- [ ] Accessibility audit (axe-core + manual) passed
- [ ] Smoke tests Stage 14 all green
- [ ] DR + incident + model-degradation runbooks reviewed (`runbooks/`)

---

## Stage 16 — Day-2: scale & cost
- **Add an agency:** new `AgencyAdapter` (`gov_platform/wog_orchestration/canonical/adapters.py`) + governed-catalog entries. No core change.
- **Add a life-event:** new template in `saga/life_events.py`. The generic Step Functions saga runs it as-is.
- **Add an agent:** deploy another `scripts/deploy.sh <agent> …`; it inherits all controls.
- **Cost monitoring:** tag everything; watch Bedrock token spend (right-size Haiku vs Sonnet), OpenSearch Serverless OCUs, DynamoDB on-demand, Step Functions transitions. Per-transaction cost falls as you add agents on the shared baseline — the platform economics improve with scale.

---

### Reference index
Architecture: `docs/SUITE-ARCHITECTURE.md`, `docs/WOG-PLATFORM-ARCHITECTURE.md` · Why the gateway: `docs/WHY-THE-MCP-LAYER.md` · Compliance: `docs/COMPLIANCE-CONTROL-MAPPINGS.md` · Sources: `SOURCES.md` · IaC: `infra/` · WoG saga deploy: `aws-native-reference/wog-platform/DEPLOY.md` · GTM: `gtm/WOG-PLATFORM-GTM-STORY.md`.
