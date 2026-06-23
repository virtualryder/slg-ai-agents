# GovOps IT Service Desk & Modernization — AWS Deployment Guide

Reference architecture mirrors the suite: CloudFront + WAF → API Gateway (Cognito JWT) → agent runtime (AgentCore Runtime container, or Step Functions + Lambda with a `waitForTaskToken` human gate) → **MCP Authorization Gateway** (AgentCore Gateway + Identity, or API Gateway + STS — portable path works in GovCloud) → connector Lambdas (ITSM (ServiceNow), Systems Manager, Security Hub/GuardDuty, KB) → Bedrock (Claude) + Guardrails + Knowledge Bases.

Cross-cutting: KMS CMK · DynamoDB append-only audit · S3 Object Lock (WORM) · CloudWatch · CloudTrail · VPC. Deploy via `infra/cloudformation/quickstart.yaml` (AgentId=07-govops-service-desk) + Terraform parity; commercial **and** GovCloud. Grounding & current AWS facts: repo-root `SOURCES.md`.
