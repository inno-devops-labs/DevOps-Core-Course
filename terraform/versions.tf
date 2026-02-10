terraform {
  required_version = ">= 1.9.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.129.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}
