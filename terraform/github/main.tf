terraform {
  required_version = ">= 1.5.0"
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

resource "github_repository" "course_repo" {
  name        = var.repo_name
  description = "DevOps course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false
}
