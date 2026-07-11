# 07-govops-service-desk — Secure Combined Deploy (P8)

Production-shaped counterpart to `infra/golden-path-07-govops-service-desk/`. **One `sam deploy`** stands up the
secure baseline **and** the full governed agent app in a single stack.

## What it provisions
- **Isolated VPC** with two private subnets; the workflow Lambdas run **in-VPC**.
- **PrivateLink VPC endpoints** (Bedrock runtime, Bedrock agent runtime, STS, Logs, **Step
  Functions**, Secrets Manager, KMS interface + **S3 / DynamoDB** gateway) + a NAT gateway.
- A **customer-managed KMS CMK** (rotation on) encrypting the **audit table**, the
  **pending-approvals table**, and **every log group** (gateway access, state machine, VPC flow).
- An **S3 Object-Lock WORM** evidence bucket (`COMPLIANCE`, CMK-encrypted, TLS-only, public
  access blocked) — the export target for finalized audit snapshots (`FinalizeFn` holds the
  scoped `s3:PutObject`).
- **VPC Flow Logs**, plus **CloudFront (TLS 1.2+) + AWS WAF** (managed rules + rate limit)
  fronting the Cognito-JWT HTTP API.
- The same governance as the base path: governed connector + gateway, the **reviewer service**
  (P7), Step Functions human gate, Bedrock Guardrail, retrieve/draft/check.

## Deploy
```bash
cd infra/golden-path-07-govops-service-desk-secure
AWS_REGION=us-east-1 ./deploy.sh slg-07-secure-dev
```
WAFv2 attaches at the CloudFront edge (not to HTTP APIs), so the secure variant deploys in
**us-east-1**. The audit/pending tables, CMK, and WORM bucket are `Retain` by design.

## Honest scope
A **reference** secure deploy for workshops and scoped pilots, not an authorized production
system: Cognito is the demo IdP, the token-signing secret is now generated in-stack (Secrets Manager) but still resolves into a Lambda env var - production should read it from Secrets Manager/KMS at runtime, WORM retention
must be set from the agency's records schedule, and ATO / StateRAMP / FedRAMP is customer work.
See `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
