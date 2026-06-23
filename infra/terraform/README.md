# Terraform parity
Identical resource topology to the CloudFormation quick-deploy, for platform teams
standardized on Terraform. `modules/` = security (KMS, Guardrail, Cognito), data
(append-only DynamoDB, WORM S3 Object Lock), gateway (portable | agentcore).
`govcloud/` is the GovCloud (US) overlay. Run: `terraform init && terraform plan`.
