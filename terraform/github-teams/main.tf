terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  owner = "devops-lab-4-owner"
  token = var.github_pat
}

resource "github_repository" "repo" {
  name             = "android-test-team-repo"
  description      = "android test team"
  visibility       = "public"
  has_issues       = true
  has_wiki         = true
  auto_init        = true
  license_template = "mit"
}

resource "github_team" "android" {
  name        = "Android Team"
  description = "DevOps guys please we don't follow best practices"
  privacy     = "closed"
}

resource "github_team" "backend" {
  name        = "Backend Team"
  description = "We propose best practices"
  privacy     = "closed"
}

resource "github_branch_default" "repo_main" {
  repository = github_repository.repo.name
  branch     = "main"
}

resource "github_branch_protection" "repo_protection" {
  repository_id                   = github_repository.repo.id
  pattern                         = github_branch_default.repo_main.branch
  require_conversation_resolution = true
  enforce_admins                  = true

  required_pull_request_reviews {
    required_approving_review_count = 1
  }
}

resource "github_team" "devops-lab4-team" {
  name        = "devops-lab4-team"
  description = "devops lab4 team"
  privacy     = "closed"
}

resource "github_team_repository" "android_repository" {
  team_id    = github_team.android.id
  repository = github_repository.repo.name
  permission = "maintain"
}

resource "github_team_repository" "backend_repository" {
  team_id    = github_team.backend.id
  repository = github_repository.repo.name
  permission = "push"
}
