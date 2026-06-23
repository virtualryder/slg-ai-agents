variable "agent_id"   { type = string  default = "01-resident-services-311" }
variable "environment"{ type = string  default = "dev" }
variable "region"     { type = string  default = "us-east-1" }
variable "gateway_mode" { type = string default = "portable" } # portable | agentcore
variable "deploy_mode"  { type = string default = "native" }   # native | container
variable "worm_retention_days" { type = number default = 2555 } # 7 years
