terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

variable "aws_profile" {
  type        = string
  description = "AWS CLI named profile used for apply and local AWS API calls."
  default     = "data-lab"
}

variable "aws_region" {
  type        = string
  description = "AWS region for the bronze landing zone."
  default     = "us-east-2"
}

variable "operator_principal_arn" {
  type        = string
  description = "Existing IAM principal ARN that receives the loader policy."
}

variable "name_prefix" {
  type        = string
  description = "Prefix for account-scoped resource names."
  default     = "datalabecom"
}
