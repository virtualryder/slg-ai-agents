# ⚠️ REFERENCE SKELETON — NOT at parity with the CloudFormation golden paths.
# CloudFormation/SAM is the canonical, validated IaC. See docs/TERRAFORM-AND-GOVCLOUD-STATUS.md
# for the coverage matrix and gaps before relying on this.

terraform {
  required_version = ">= 1.5"
  required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}
provider "aws" { region = var.region }

module "security" {
  source      = "./modules/security"
  agent_id    = var.agent_id
  environment = var.environment
}
module "data" {
  source        = "./modules/data"
  agent_id      = var.agent_id
  environment   = var.environment
  kms_key_arn   = module.security.kms_key_arn
  worm_retention_days = var.worm_retention_days
}
module "gateway" {
  source        = "./modules/gateway"
  agent_id      = var.agent_id
  environment   = var.environment
  gateway_mode  = var.gateway_mode
}

output "guardrail_id"   { value = module.security.guardrail_id }
output "audit_table"    { value = module.data.audit_table_name }
output "worm_bucket"    { value = module.data.worm_bucket_name }
