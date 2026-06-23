# Benefits / HHS Caseworker Assist — AWS Deployment Guide

Reference architecture mirrors the suite: CloudFront + WAF → API Gateway (Cognito JWT) → agent runtime (AgentCore Runtime container, or Step Functions + Lambda with a `waitForTaskToken` human gate) → MCP Authorization Gateway (AgentCore Gateway + Identity, or API Gateway + STS — portable path works in GovCloud) → connector Lambdas (Integrated eligibility system, IDP, Identity, KB) → Bedrock (Claude) + Guardrails + Knowledge Bases. Cross-cutting: KMS CMK · DynamoDB append-only audit · S3 Object Lock (WORM) · CloudWatch · CloudTrail · VPC.

Deploy: `scripts/deploy.sh 04-benefits-caseworker dev portable native`. Full step-by-step: `runbooks/WOG-PLATFORM-DEPLOYMENT-RUNBOOK.md`. Sources: `SOURCES.md`.
