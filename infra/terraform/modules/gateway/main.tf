variable "agent_id" {}
variable "environment" {}
variable "gateway_mode" { default = "portable" }
# portable -> API Gateway HTTP API + Cognito JWT authorizer (any region, incl. GovCloud)
# agentcore -> Bedrock AgentCore Gateway + Identity (AgentCore regions only)
resource "aws_apigatewayv2_api" "gateway" {
  count         = var.gateway_mode == "portable" ? 1 : 0
  name          = "slg-${var.agent_id}-${var.environment}-gateway"
  protocol_type = "HTTP"
}
output "gateway_mode" { value = var.gateway_mode }
