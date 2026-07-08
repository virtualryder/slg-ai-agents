# Terraform & GovCloud status — SLG AI Agent Suite

**Honest status.** CloudFormation/SAM is the **canonical, validated** IaC for this suite (all eight
golden paths were deployed and torn down in a live account — see
[`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)). The Terraform
under `infra/terraform/` is **a reference skeleton, not at parity** with the CloudFormation golden
paths. Earlier docs described it as "Terraform parity"; that overstated it and has been corrected.
This document is the accurate picture.

## Coverage: Terraform vs the CloudFormation golden path

The Terraform reproduces ~10 AWS resource *types*; the golden-path CloudFormation uses ~41. What the
Terraform skeleton covers vs. what it does not:

| Control / resource | CloudFormation golden path | Terraform skeleton |
|---|---|---|
| KMS CMK + alias | ✅ | ✅ |
| DynamoDB audit + approvals tables | ✅ (append-only IAM deny) | ✅ (tables only; IAM deny not wired) |
| S3 WORM (Object Lock) | ✅ | ✅ (bucket + lock config) |
| Bedrock Guardrail | ✅ | ✅ |
| Cognito user pool | ✅ (+ client, JWT authorizer) | ⚠️ pool only |
| MCP/tool gateway | ✅ API GW HTTP API + **Cognito JWT authorizer + routes + integration** | ❌ **bare `aws_apigatewayv2_api` only — no authorizer, routes, or integration** |
| Workflow (Step Functions) | ✅ | ❌ absent |
| Workflow/connector Lambdas | ✅ (least-privilege roles) | ❌ absent |
| VPC / subnets / endpoints (secure variant) | ✅ | ❌ absent |
| CloudFront + WAF edge (secure variant) | ✅ | ❌ absent |

**Bottom line:** the Terraform is a *starting skeleton* an engagement can grow; it is **not** a
drop-in equivalent of the CloudFormation deploy today.

## GovCloud posture

- `infra/terraform/govcloud/main.tf` is a **~12-line overlay** that pins the region to `us-gov-west-1`
  and forces `gateway_mode = "portable"`. It is a **design-time overlay, not deployed** — no
  `terraform apply` in GovCloud has been performed.
- The pin to the portable gateway is correct and deliberate: Bedrock + Guardrails + Knowledge Bases
  are FedRAMP High / DoD IL-4/5 in GovCloud, but **AgentCore Gateway (semantic search / Memory /
  Policy / Registry) was not yet in GovCloud as of 2026-05** — so the managed-gateway path is
  unavailable there and the portable API-Gateway-+-Cognito path is the only option.
- GovCloud partition differences (ARNs `aws-us-gov`, service availability, endpoint names) are **not**
  fully abstracted in the skeleton; a real GovCloud deployment is engagement work.

## What "done" would require (engagement-owned)

Grow the Terraform to the golden-path resource set (authorizer + routes + integration, Step Functions,
Lambdas with least-privilege, VPC/endpoints for the secure profile, the audit-table IAM deny), run
`terraform validate` / `plan` / `apply` in a commercial account, then repeat in GovCloud. Until then,
**deploy with CloudFormation/SAM** (the canonical path) and treat Terraform as reference.
