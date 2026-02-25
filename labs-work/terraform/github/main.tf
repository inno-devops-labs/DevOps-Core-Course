terraform {
  required_version = ">= 1.5"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {}

resource "github_repository" "devops_course" {
  name        = "DevOps-Core-Course"
  description = "DevOps course repository - Infrastructure as Code, CI/CD, containers, and more"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false

  lifecycle {
    prevent_destroy = true
  }
}
