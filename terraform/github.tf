# GitHub Provider Configuration for Repository Management
# This file demonstrates importing existing infrastructure into Terraform
# Note: required_providers for github is defined in main.tf

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

# Import existing DevOps-Core-Course repository
resource "github_repository" "devops_course" {
  name        = "DevOps-Core-Course"
  description = "DevOps Engineering: Core Practices - Lab assignments and projects"
  visibility  = "public"

  has_issues    = true
  has_wiki      = false
  has_projects  = false
  has_downloads = true

  allow_merge_commit = true
  allow_squash_merge = true
  allow_rebase_merge = true
  allow_auto_merge   = false

  delete_branch_on_merge = true

  topics = [
    "devops",
    "terraform",
    "pulumi",
    "docker",
    "kubernetes",
    "ansible",
    "ci-cd",
    "infrastructure-as-code"
  ]
}

# Branch protection for master branch (optional)
resource "github_branch_protection" "master_protection" {
  repository_id = github_repository.devops_course.node_id
  pattern       = "master"

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = false
    required_approving_review_count = 0
  }

  enforce_admins = false
}