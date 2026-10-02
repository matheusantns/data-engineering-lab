locals {
  operator_is_user = can(regex(":user/", var.operator_principal_arn))
  operator_is_role = can(regex(":role/", var.operator_principal_arn))
  operator_name    = element(split("/", var.operator_principal_arn), length(split("/", var.operator_principal_arn)) - 1)
}

data "aws_iam_policy_document" "loader" {
  statement {
    sid     = "ListBronzePrefix"
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.bronze.arn,
    ]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["bronze/*"]
    }
  }

  statement {
    sid = "ReplaceBronzePartition"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.bronze.arn}/bronze/*",
    ]
  }

  statement {
    sid     = "ListAthenaResults"
    actions = ["s3:ListBucket"]
    resources = [
      aws_s3_bucket.athena_results.arn,
    ]
  }

  statement {
    sid = "WriteAthenaResults"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.athena_results.arn}/*",
    ]
  }

  statement {
    sid = "ReadGlueCatalog"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/ecommerce_bronze",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/ecommerce_bronze/*",
    ]
  }

  statement {
    sid = "RunAthenaQueries"
    actions = [
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StopQueryExecution",
      "athena:GetWorkGroup",
    ]
    resources = [
      "arn:aws:athena:${var.aws_region}:${data.aws_caller_identity.current.account_id}:workgroup/*",
    ]
  }
}

resource "aws_iam_policy" "loader" {
  name   = "${var.name_prefix}-bronze-loader"
  policy = data.aws_iam_policy_document.loader.json
}

resource "aws_iam_user_policy_attachment" "loader" {
  count      = local.operator_is_user ? 1 : 0
  user       = local.operator_name
  policy_arn = aws_iam_policy.loader.arn
}

resource "aws_iam_role_policy_attachment" "loader" {
  count      = local.operator_is_role ? 1 : 0
  role       = local.operator_name
  policy_arn = aws_iam_policy.loader.arn
}
