data "aws_caller_identity" "current" {}

locals {
  bronze_bucket_name = "${var.name_prefix}-bronze-${data.aws_caller_identity.current.account_id}"
  athena_bucket_name = "${var.name_prefix}-athena-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "bronze" {
  bucket = local.bronze_bucket_name
}

resource "aws_s3_bucket" "athena_results" {
  bucket = local.athena_bucket_name
}

resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket                  = aws_s3_bucket.bronze.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket                  = aws_s3_bucket.athena_results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
