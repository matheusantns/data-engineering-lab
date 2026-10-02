output "bronze_bucket" {
  description = "S3 bucket name for bronze Parquet landings."
  value       = aws_s3_bucket.bronze.bucket
}

output "athena_results_bucket" {
  description = "S3 bucket name for Athena query results."
  value       = aws_s3_bucket.athena_results.bucket
}

output "athena_workgroup" {
  description = "Athena workgroup used for bronze sanity queries."
  value       = aws_athena_workgroup.bronze.name
}

output "glue_database" {
  description = "Glue Data Catalog database for ecommerce bronze tables."
  value       = aws_glue_catalog_database.ecommerce_bronze.name
}
