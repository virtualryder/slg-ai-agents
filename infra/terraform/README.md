# Terraform — reference skeleton (NOT parity)

> **Status:** this is a reference skeleton, **not** at parity with the CloudFormation golden paths. CloudFormation/SAM is the canonical, validated IaC. See [`../../docs/TERRAFORM-AND-GOVCLOUD-STATUS.md`](../../docs/TERRAFORM-AND-GOVCLOUD-STATUS.md) for the exact coverage matrix and gaps.

Identical resource topology to the CloudFormation quick-deploy, for platform teams
standardized on Terraform. `modules/` = security (KMS, Guardrail, Cognito), data
(append-only DynamoDB, WORM S3 Object Lock), gateway (portable | agentcore).
`govcloud/` is the GovCloud (US) overlay. Run: `terraform init && terraform plan`.
