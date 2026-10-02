locals {
  catalog_tables = {
    for table in yamldecode(file("${path.module}/../catalog/tables.yaml")).tables :
    table.name => table
  }
}

resource "aws_glue_catalog_database" "ecommerce_bronze" {
  name = "ecommerce_bronze"
}

resource "aws_glue_catalog_table" "ecommerce_bronze" {
  for_each = local.catalog_tables

  name          = each.key
  database_name = aws_glue_catalog_database.ecommerce_bronze.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                      = "TRUE"
    classification                = "parquet"
    "projection.enabled"          = "true"
    "projection.dt.type"          = "date"
    "projection.dt.format"        = "yyyy-MM-dd"
    "projection.dt.range"         = "2026-01-01,NOW"
    "projection.dt.interval"      = "1"
    "projection.dt.interval.unit" = "DAYS"
    "storage.location.template"   = "s3://${aws_s3_bucket.bronze.bucket}/bronze/${each.key}/dt=$${dt}/"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.bronze.bucket}/bronze/${each.key}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    dynamic "columns" {
      for_each = each.value.columns
      content {
        name = columns.value.name
        type = columns.value.type
      }
    }
  }

  partition_keys {
    name = "dt"
    type = "string"
  }
}
