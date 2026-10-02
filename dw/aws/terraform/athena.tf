resource "aws_athena_workgroup" "bronze" {
  name = "${var.name_prefix}-bronze"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/"
    }
  }
}
