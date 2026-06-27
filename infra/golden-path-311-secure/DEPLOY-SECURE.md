# 311 — Secure Combined Deploy (P8)

This is the **production-shaped** counterpart to `infra/golden-path-311/`. Where the base
golden path deploys the governed agent app as a quick skeleton, this template provisions the
**secure baseline and the app in one `sam deploy`** so the deployed picture matches the
architecture diagrams a CISO reviews.

## What one command stands up
**Secure baseline (in the same stack):**
- An **isolated VPC** with two private subnets; the workflow Lambdas run **in-VPC** (`VpcConfig`).
- **PrivateLink VPC endpoints** so the Lambdas reach AWS without traversing the internet:
  Bedrock runtime, Bedrock **agent** runtime (KB retrieval), STS, CloudWatch Logs, **Step
  Functions** (the reviewer's `SendTaskSuccess`), Secrets Manager, KMS (interface) + **S3 and
  DynamoDB** (gateway). A NAT gateway covers any residual egress.
- A **customer-managed KMS CMK** (rotation on) that encrypts the **audit table**, the
  **pending-approvals table**, and **every log group** (gateway access, state machine, VPC flow).
- An **S3 Object-Lock WORM** evidence bucket (`COMPLIANCE` mode, CMK-encrypted, TLS-only,
  public access blocked) — the immutable export target for finalized audit snapshots
  (`AUDIT_WORM_BUCKET`; `FinalizeFn` holds the scoped `s3:PutObject`).
- **VPC Flow Logs** to an encrypted log group.

**The app (identical governance to the base path):** the five workflow Lambdas
(classify → retrieve → draft → check → **human gate** → finalize), the governed connector,
the **reviewer service** (P7), the Step Functions state machine, Cognito + the **HTTP API
behind a Cognito JWT authorizer**, the Bedrock Guardrail, and the audit + pending tables.

**Edge:** **CloudFront (TLS 1.2+) + AWS WAF** (Common + Known-Bad-Inputs managed rules + a
rate-based rule) front the API. WAFv2 does not attach to HTTP APIs, so protection is applied
at the CloudFront edge — which is why this variant must be deployed in **us-east-1**.

## Deploy
```bash
cd infra/golden-path-311-secure
AWS_REGION=us-east-1 ./deploy.sh slg-311-secure-dev
```
Tear down with `sam delete --stack-name slg-311-secure-dev`. The audit/pending tables, KMS key,
and WORM bucket are `Retain` by design (evidence must outlive the stack); remove them manually
after exporting evidence.

## Adopting this for agents 02–08
The secure baseline block (KMS + VPC + endpoints + WORM + edge) and the four wiring changes —
`VpcConfig` in `Globals`, CMK on the two tables, `KmsKeyId` on the log groups, and the
CloudFront/WAF front — are agent-independent. Apply the same block to any
`infra/golden-path-0X-*/template.yaml` (swap the `slg-311` name prefix and the guardrail logical
id) to make that agent a secure combined deploy. 311 is the worked reference.

## Honest scope
This is a **reference** secure deploy for workshops and scoped pilots, not an authorized
production system. Cognito is the demo IdP (production federates the agency IdP); `TokenSecret`
must move to Secrets Manager/KMS; WORM retention must be set from the agency's records schedule;
and an ATO / StateRAMP / FedRAMP authorization is customer-engagement work. See
`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
