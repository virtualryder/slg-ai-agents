variable "agent_id" {}
variable "environment" {}
variable "kms_key_arn" {}
variable "worm_retention_days" { default = 2555 }

resource "aws_dynamodb_table" "audit" {
  name         = "slg-${var.agent_id}-${var.environment}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "audit_id"
  range_key    = "ts"
  attribute { name = "audit_id" type = "S" }
  attribute { name = "ts"       type = "S" }
  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true kms_key_arn = var.kms_key_arn }
}
resource "aws_s3_bucket" "worm" {
  bucket              = "slg-${var.agent_id}-${var.environment}-worm"
  object_lock_enabled = true
}
resource "aws_s3_bucket_object_lock_configuration" "worm" {
  bucket = aws_s3_bucket.worm.id
  rule { default_retention { mode = "COMPLIANCE" days = var.worm_retention_days } }
}
resource "aws_s3_bucket_versioning" "worm" {
  bucket = aws_s3_bucket.worm.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_public_access_block" "worm" {
  bucket                  = aws_s3_bucket.worm.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
output "audit_table_name" { value = aws_dynamodb_table.audit.name }
output "worm_bucket_name" { value = aws_s3_bucket.worm.id }
