# Agent 01 — AWS Deployment Guide

## Reference architecture
```
Resident (web / mobile / chat / voice)
        │
   CloudFront + AWS WAF
        │
   API Gateway (HTTP API)  ──►  Cognito (User Pool / Identity Center → agency IdP)
        │
   Agent runtime
     • AgentCore Runtime (ARM64 container, /invocations + /ping)   ← container mode
     • Step Functions + Lambda (waitForTaskToken HITL gate)        ← native mode
        │
   MCP Authorization Gateway
     • AgentCore Gateway + AgentCore Identity   (AgentCore regions)
     • API Gateway + Lambda authorizer + STS    (portable / any region / GovCloud)
        │
   Connector Lambdas (one per system of record): 311/CRM · KB · Identity · Scheduling · GIS
        │
   Systems of record + Bedrock Knowledge Base (OpenSearch Serverless / Aurora pgvector)

Cross-cutting: Bedrock (Claude) + Guardrails · KMS CMK · DynamoDB append-only audit ·
S3 Object Lock (WORM) snapshots · CloudWatch · CloudTrail · VPC (private subnets, Bedrock VPC endpoint)
```

## Grounding (current AWS facts)
- **Amazon Bedrock AgentCore** is GA (Oct 13, 2025); components: Runtime, Memory, Gateway, Identity, Code Interpreter, Browser, Observability.
- **AgentCore Gateway** turns Lambdas/APIs/MCP servers into governed agent tools; **AgentCore Identity** issues scoped, delegated tokens (Cognito/Okta/Entra/Auth0).
- **GovCloud:** Bedrock + Agents + Guardrails + Knowledge Bases are FedRAMP High / DoD IL-4/5 approved (May 23, 2025). AgentCore launched in GovCloud (US-West) May 5, 2026 — **Memory, Gateway semantic search, Policy, Registry are NOT yet in GovCloud**, so GovCloud deployments use the **portable** gateway path (API Gateway + Lambda authorizer + STS). See `../../docs/COMPLIANCE-CONTROL-MAPPINGS.md` and `SOURCES.md`.

## Two deploy modes (`DeployMode`) and two gateway paths (`GatewayMode`)
Identical to the suite IaC: `native` (Step Functions + Lambda) or `container` (ECS Fargate / AgentCore Runtime); `portable` (any region, incl. GovCloud) or `agentcore`. Migrating portable→agentcore changes only the gateway stack.

## Quick deploy
```bash
scripts/build_lambdas.sh 01-resident-services-311
CFN_BUCKET=my-cfn CODE_BUCKET=my-code \
  scripts/deploy.sh 01-resident-services-311 dev portable native
```
See `../../infra/` for the CloudFormation master + Terraform parity (commercial + GovCloud).
