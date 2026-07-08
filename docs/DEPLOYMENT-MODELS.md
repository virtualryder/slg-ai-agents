# Deployment Models — Standalone Agent vs. Whole-of-Government

**Short answer: the Whole-of-Government (WoG) platform is NOT a prerequisite. Every agent deploys standalone with its own complete, secure, governed architecture. The WoG is an optional, additive layer you adopt later — agent by agent — when the institution is ready to coordinate across agencies. The same agents plug into it with no rewrite.**

---

## Model A — Standalone Agent (the default starting point)
Deploy a single agent into a customer-isolated environment with **no WoG dependency**. One command (`scripts/deploy.sh <agent> <env> <gateway> <mode>`) deploys `infra/cloudformation/quickstart.yaml`, which nests a **complete standalone stack**:

| Layer | Stack | What you get |
|---|---|---|
| **Edge / front-end** | `edge.yaml` | **Amazon CloudFront (TLS 1.2+) + AWS WAF** (managed rules: OWASP, known-bad-inputs, IP reputation, rate-limit) + **AWS Shield** |
| **Identity** | `security.yaml` (Cognito) | **Amazon Cognito** federates the agency IdP and issues a short-lived **JWT**; API Gateway's Cognito JWT authorizer validates it; the gateway re-checks the `custom:slg_role` claim and mints a scoped per-call token |
| **Network** | `network.yaml` | Own VPC · private subnets · NAT · **Bedrock VPC interface endpoint** (private connectivity to the regional Bedrock service) · S3 gateway endpoint · **VPC Flow Logs** |
| **Security** | `security.yaml` | **KMS CMK** (rotation on) · **Bedrock Guardrail** (PII/denied-topics/grounding) · **Cognito** (federate your IdP) · least-privilege agent role |
| **Data / logging** | `data.yaml` | **Append-only DynamoDB audit** (PITR) · **S3 Object Lock (WORM)** · HITL queue table |
| **Gateway** | `gateway-portable.yaml` / `agentcore-gateway.yaml` | Deny-by-default MCP authorization gateway (portable works in GovCloud) |
| **Agent** | `agent-service.yaml` | Step Functions + Lambda (`waitForTaskToken` human gate) or ECS/AgentCore Runtime |
| Cross-cutting | — | CloudWatch · CloudTrail · data-class isolation (CJI/FTI/PHI/EDU/public) |

**This is a full, defensible, audited deployment by itself.** A CISO gets least-privilege authorization, WORM audit, KMS encryption, private inference, and a human gate — for one agent, in its own boundary. Step-by-step: each agent's `docs/DEPLOY-RUNBOOK.md`.

**Grow agent by agent.** Deploy Resident Services first; add Forms, then Permitting, then Benefits — each in its own isolated stack, each immediately useful, each producing audit evidence. No big-bang program required.

## Model B — Whole-of-Government (additive, when ready)
When the institution wants to coordinate **across** agencies — organize services around a resident's life event (move, job loss, new business, disaster, bereavement) — deploy the WoG platform **in addition** (`infra/cloudformation/wog-platform.yaml`): the EventBridge compliance bus, consent + event + idempotency DynamoDB stores, WORM evidence bucket, and the durable Step Functions saga. The **same standalone agents become steps** in the saga — no rewrite. The orchestrator holds no tool grants; every write still flows through each agent's own deny-by-default gateway.

| | Model A — Standalone | Model B — + WoG |
|---|---|---|
| WoG required? | **No** | n/a |
| Scope | one agency / workflow | cross-agency life events |
| Each agent's own VPC/KMS/WORM/audit/gateway | ✅ | ✅ (unchanged) |
| Cross-agency consent + saga + compensation | — | ✅ |
| Best for | "help us start, securely, now" | "coordinate the whole of government" |

**Migration is purely additive:** standalone agents keep running; deploying the WoG stack and registering them as saga steps adds cross-agency orchestration on top. Nothing about the agent changes.

## The pitch
*"You don't have to go all-in on a whole-of-government program to get value. We'll stand up one agent — its own VPC, KMS, WORM audit trail, guardrails, and human gate — and prove it in front of your CISO. When you're ready, the same agents become a coordinated platform. Secure and governed from agent one."*
