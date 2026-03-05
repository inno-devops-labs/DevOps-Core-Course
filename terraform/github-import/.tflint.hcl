plugin "terraform" {
  enabled = true
}

plugin "github" {
  enabled = true
  version = "0.41.0"
  source  = "github.com/terraform-linters/tflint-ruleset-github"
}
