plugin "terraform" {
  enabled = true
}

plugin "yandex" {
  enabled = true
  version = "0.1.0"
  source  = "github.com/terraform-linters/tflint-ruleset-yandex"
}
