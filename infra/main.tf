module "aws" {
  source = "./aws"
}

provider "aws" {
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  version                     = "2.67.0"

  endpoints {
    dynamodb = "http://localhost:8022"
  }
}

terraform {
  backend "local" {}
}
