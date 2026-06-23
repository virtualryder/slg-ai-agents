variable "agent_id" {}
variable "environment" {}

resource "aws_kms_key" "agent" {
  description         = "CMK for SLG agent ${var.agent_id} (${var.environment})"
  enable_key_rotation = true
}
resource "aws_kms_alias" "agent" {
  name          = "alias/slg-${var.agent_id}-${var.environment}"
  target_key_id = aws_kms_key.agent.key_id
}
resource "aws_bedrock_guardrail" "resident" {
  name                      = "slg-${var.agent_id}-${var.environment}"
  blocked_input_messaging   = "I can't help with that request."
  blocked_outputs_messaging = "I can't provide that information."
  sensitive_information_policy_config {
    pii_entities_config { type = "US_SOCIAL_SECURITY_NUMBER" action = "BLOCK" }
    pii_entities_config { type = "CREDIT_DEBIT_CARD_NUMBER"  action = "BLOCK" }
    pii_entities_config { type = "DRIVER_ID"                 action = "ANONYMIZE" }
    pii_entities_config { type = "EMAIL"                     action = "ANONYMIZE" }
  }
}
resource "aws_cognito_user_pool" "this" {
  name = "slg-${var.agent_id}-${var.environment}"
  schema {
    name                = "slg_role"
    attribute_data_type = "String"
    mutable             = true
  }
}
output "kms_key_arn"  { value = aws_kms_key.agent.arn }
output "guardrail_id" { value = aws_bedrock_guardrail.resident.guardrail_id }
output "user_pool_id" { value = aws_cognito_user_pool.this.id }
