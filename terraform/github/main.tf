terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
}

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps Core Course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false

  allow_merge_commit = true
  allow_squash_merge = true
  allow_rebase_merge = true
}
