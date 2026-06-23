# GovCloud (US) overlay — forces the portable gateway path and the GovCloud region.
# Bedrock + Guardrails + Knowledge Bases are FedRAMP High / DoD IL-4/5 in GovCloud.
# AgentCore Gateway semantic search / Memory / Policy / Registry are NOT yet in
# GovCloud (as of 2026-05), so gateway_mode is pinned to "portable".
module "slg" {
  source              = "../"
  region              = "us-gov-west-1"
  gateway_mode        = "portable"
  environment         = "prod"
  worm_retention_days = 2555
}
