# Procurement, Contracting & Grants — AWS Deployment Guide

Reference architecture mirrors the suite: CloudFront + WAF → API Gateway (Cognito JWT) → agent runtime (AgentCore Runtime container, or Step Functions + Lambda with a `waitForTaskToken` human gate) → MCP Authorization Gateway (AgentCore Gateway + Identity, or API Gateway + STS — portable path works in GovCloud) → connector Lambdas (ERP/e-procurement, grants systems, IDP, KB) → Bedrock (Claude) + Guardrails + Knowledge Bases. Cross-cutting: KMS CMK · DynamoDB append-only audit · S3 Object Lock (WORM) · CloudWatch · CloudTrail · VPC.

Deploy: `scripts/deploy.sh 06-procurement-grants dev portable native`. Full step-by-step: `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`. Sources: `SOURCES.md`.
