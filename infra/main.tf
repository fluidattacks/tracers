module "aws" {
  source = "./aws"
}

variable "dynamo_endpoint" {
  type = string
}

provider "aws" {
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  version                     = "2.67.0"

  endpoints {
    dynamodb = var.dynamo_endpoint
  }
}

terraform {
  backend "local" {}
}
