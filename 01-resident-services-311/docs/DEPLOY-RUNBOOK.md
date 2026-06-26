# Resident Services & 311 Navigator — AWS Deployment Runbook (step-by-step)
*Audience: an AWS Solutions Architect or customer cloud engineer deploying Agent 01 (`01-resident-services-311`) into a real AWS account — commercial or GovCloud. This is a follow-along guide: run each numbered step, then confirm the **Verify** line before moving on. Total hands-on time once the shared foundation exists: ~45–90 min.*

> **Fastest path — the wired golden path.** For a true one-command deploy of the *real* agent (the five workflow Lambdas, the actual Step Functions ASL with the `waitForTaskToken` human gate, an HTTP API with a Cognito JWT authorizer + access logging + throttling, and per-function least-privilege roles), use the SAM app at **`infra/golden-path-311/`** — `./deploy.sh` then `./smoke_test.sh`. This runbook below documents the underlying components and the standalone secure-stack model in more detail.

> **Standalone deployment — no WoG required.** The standalone stack gives this agent its **own VPC + Flow Logs + Bedrock VPC endpoint**, **CloudFront + AWS WAF + Shield** edge, KMS CMK, Bedrock Guardrail, **Cognito (IdP federation → JWT)**, audit + S3 Object Lock (WORM), the deny-by-default gateway, and the agent — with **no dependency on the Whole-of-Government platform**. Adopt the WoG layer later (it's additive). See `../../docs/DEPLOYMENT-MODELS.md`. *(Append-only audit enforcement and data-class WORM retention are tracked in `docs/REPO-REVIEW-AND-REMEDIATION-PLAN.md` P2.)*

---
## 0. Prerequisites (≈15 min) — confirm before you start
1. **Tools installed:** `aws` CLI v2, `python3.12`, `git`, `zip` (and `docker` only if you choose container mode). Verify:
   ```bash
   aws --version && python3 --version && git --version
   ```
2. **AWS access:** an admin/deploy role in the target account; run `aws sts get-caller-identity` and confirm the account ID is the intended one.
3. **Decisions:** Region posture (commercial | GovCloud), `GatewayMode` (`portable` works everywhere incl. GovCloud | `agentcore`), `DeployMode` (`native` Step Functions+Lambda | `container` ECS/AgentCore Runtime).
4. **IdP:** the agency identity provider (SAML/OIDC) ready to federate into Cognito, with a group that will map to `custom:slg_role = RESIDENT_SERVICES_AGENT`.
5. **Two S3 buckets** in the account: a CloudFormation staging bucket and a Lambda code bucket.
   ```bash
   export CFN_BUCKET=my-cfn-bucket CODE_BUCKET=my-code-bucket REGION=us-east-1
   aws s3 mb s3://$CFN_BUCKET --region $REGION ; aws s3 mb s3://$CODE_BUCKET --region $REGION
   ```
**Verify:** `aws sts get-caller-identity` returns the right account, and both buckets exist (`aws s3 ls | grep my-`).

## 1. Prove it locally first (≈5 min, no AWS spend)
```bash
cd 01-resident-services-311
pip install -e ../platform_core && pip install langgraph
EXTRACT_MODE=demo python demo/demo_run.py
PYTHONPATH=../platform_core:..:. python -m pytest tests -q
```
**Verify:** the demo prints each intent → action → outcome, and the tests report all passed/skipped. If this fails, fix it before any AWS step.

## 2. Shared foundation (≈30 min, once per account — skip if already done)
Follow **Stages 1–7 of `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`** (it has the exact commands): Org/landing zone + data-class isolation → networking (VPC + Bedrock VPC endpoint + WAF) → KMS CMK → Cognito federated to your IdP → Bedrock model access + Guardrail → Knowledge Base → MCP gateway path.
**Verify:** you can capture these four outputs (you will reuse them):
```bash
export KMS_ARN=$(aws cloudformation describe-stacks --stack-name slg-sec-dev --query "Stacks[0].Outputs[?OutputKey=='KmsKeyArn'].OutputValue" --output text)
export GUARDRAIL_ID=$(aws cloudformation describe-stacks --stack-name slg-sec-dev --query "Stacks[0].Outputs[?OutputKey=='GuardrailId'].OutputValue" --output text)
echo "KMS=$KMS_ARN  GUARDRAIL=$GUARDRAIL_ID"   # both must be non-empty
```

## 3. Map this agent's role in your IdP (≈5 min)
In Cognito, map the agency IdP group for this workflow to the custom attribute `custom:slg_role = RESIDENT_SERVICES_AGENT`.
**Why:** the gateway authorizes `agent grant ∩ user entitlement`, so only users with `RESIDENT_SERVICES_AGENT` can drive this agent, and only for its granted tools: `crm311.create_service_request`, `kb.search_policy`, `identity.verify_resident`, `scheduling.book_appointment`, `gis.get_parcel`.
**Verify:** sign in as a test user and decode the JWT (jwt.io or `aws cognito-idp ...`) — confirm `custom:slg_role` contains `RESIDENT_SERVICES_AGENT`.

## 4. Point the connectors at this agent's systems (≈10 min)
Systems of record: **311/CRM · KB · Identity · Scheduling · GIS**. For each, either implement the agency adapter in `platform_core/slg_agent_platform/connectors/live.py`, **or** set the REST base URL for the bundled adapter, e.g.:
```bash
export CRM311_BASE_URL=https://crm311.youragency.gov
```
Method signatures match the fixtures, so no agent code changes between demo and live.
**Verify:** `CONNECTOR_MODE=live python -c "from slg_agent_platform.connectors import get_connector; print(get_connector('crm311'))"` returns the HTTP adapter (not the NotImplemented stub).

## 5. Package the agent (≈5 min)
```bash
scripts/build_lambdas.sh 01-resident-services-311
aws s3 cp .build/01-resident-services-311-lambdas.zip s3://$CODE_BUCKET/
aws s3 sync infra/cloudformation s3://$CFN_BUCKET/slg --exclude "README.md"
```
**Verify:** `aws s3 ls s3://$CODE_BUCKET/01-resident-services-311-lambdas.zip` shows the object.

## 6. Deploy the agent stack (≈10 min)
```bash
scripts/deploy.sh 01-resident-services-311 dev portable native
#                 ^AgentId  ^env ^GatewayMode ^DeployMode   (use 'portable' in GovCloud)
```
This nests **security** (KMS, Bedrock Guardrail, Cognito, least-privilege role), **data** (append-only DynamoDB audit, S3 Object Lock WORM, HITL table), **gateway**, and **agent** stacks for `AgentId=01-resident-services-311`.
**Verify:** `aws cloudformation describe-stacks --stack-name slg-01-resident-services-311-dev --query "Stacks[0].StackStatus"` returns `CREATE_COMPLETE`.

## 7. Make the Guardrail mandatory for this agent (≈3 min)
```bash
export BEDROCK_GUARDRAIL_ID=$GUARDRAIL_ID BEDROCK_GUARDRAIL_VERSION=DRAFT ENVIRONMENT=production
```
Confirm the Guardrail blocks/masks PII (SSN/bank/card BLOCK; driver-ID/email/phone ANONYMIZE), denies out-of-scope determinations, and runs contextual grounding checks on drafting.
**Verify:** with `ENVIRONMENT=production` and **no** guardrail set, the LLM factory refuses to start (fail-closed) — that proves the control is enforced.

## 8. Wire the human-in-the-loop gate (≈10 min)
The `human_review_gate` runs as a Step Functions `waitForTaskToken` state: the execution pauses and notifies a reviewer (SNS/SES or your console) with the draft + task token; the reviewer approves and your app calls `SendTaskSuccess` with the approval payload. Operate per `runbooks/HITL-QUEUE-OPERATIONS.md`.
**Verify:** start a write-path execution (step 9.2) and confirm it enters `WAIT` at `HumanGate`, then resumes on `SendTaskSuccess`.

## 9. Smoke tests (≈10 min — all must pass before go-live)
1. **Read path:** invoke the agent with a benign request — e.g. *"How do I find my trash pickup day?"* — and confirm a grounded, cited response. **Verify:** response returns with citations; grounding flag true.
2. **Write path:** drive an action that calls `crm311.create_service_request`; confirm it **PAUSES** at the gate, then approve and confirm the write commits. **Verify:** the action appears in the audit DynamoDB table with `decision=ALLOW` and an `approved_by` reviewer.
3. **Authorization:** call a tool this role is **not** entitled to. **Verify:** `decision=DENY` in the audit table.
4. **Accessibility:** run `governance/accessibility` checks on a generated response. **Verify:** no WCAG failures.

## 10. Go-live checklist
- [ ] `RESIDENT_SERVICES_AGENT` IdP mapping verified end-to-end (step 3)
- [ ] Connectors validated against live systems (step 4)
- [ ] Guardrail attached and mandatory, `ENVIRONMENT=production` (step 7)
- [ ] Audit append-only (SCP denies Update/Delete) + WORM retention set to the records schedule
- [ ] HITL queue operational; approver-identity enforcement tested (step 8)
- [ ] All smoke tests green (step 9); accessibility audit passed
- [ ] DR / incident / model-degradation runbooks reviewed (`runbooks/`)

## 11. AWS-native variant (optional)
`aws-native-reference/01-resident-services-311/` is the Strands + Step Functions rebuild (deterministic core + 5 Lambdas + `*.asl.json` with a `waitForTaskToken` gate); see its `DEPLOY.md`.
