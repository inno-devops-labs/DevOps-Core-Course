plugin "terraform" {
  enabled = true
}

plugin "aws" {
  enabled = true
  version = "0.38.1"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
