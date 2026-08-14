terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state -- point this at your own bucket/table before `terraform init`.
  backend "s3" {
    bucket         = "REPLACE_ME-ecommerce-tfstate"
    key            = "ecommerce-microservices/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "REPLACE_ME-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
