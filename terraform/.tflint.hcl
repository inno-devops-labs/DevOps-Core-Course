plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "yandex" {
  enabled = true
  version = "0.1.0"
  source  = "github.com/yandex-cloud/tflint-ruleset-yandex-cloud"
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_deprecated_index" {
  enabled = true
}