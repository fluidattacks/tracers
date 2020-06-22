resource "aws_dynamodb_table" "main" {
  name           = "main"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "hash_key"
  range_key      = "range_key"

  attribute {
    name = "hash_key"
    type = "S"
  }

  attribute {
    name = "range_key"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }
}
