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
  owner = var.github_owner
}

# Get the authenticated user's data
data "github_user" "current" {
  username = ""
}

# Repository resource definition
resource "github_repository" "course_repo" {
  name        = var.repo_name
  description = "DevOps course lab assignments - Core infrastructure practices"
  visibility  = "public"

  has_issues    = true
  has_wiki      = false
  has_projects  = false
  has_downloads = true

  # Security settings
  security_and_analysis {
    secret_scanning                 = true
    secret_scanning_push_protection = true
    advanced_security               = false
  }

  topics = [
    "devops",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "ci-cd",
    "infrastructure",
    "learning"
  ]

  # License
  license_template = "mit"

  # Default branch (if creating new repo, not used for import)
  # default_branch = "master"

  # Delete branch on merge (optional)
  allow_auto_merge       = false
  allow_merge_commit     = true
  allow_rebase_merge     = true
  allow_squash_merge     = true
  delete_branch_on_merge = false

  # Webhooks (optional - can be added later)
  # lifecycle {
  #   ignore_changes = [webhook]
  # }

  tags = {
    Course    = "DevOps-Core-Course"
    ManagedBy = "Terraform"
  }
}

# Branch protection for master (optional, recommended)
# resource "github_branch_protection" "master_protection" {
#   repository_id = github_repository.course_repo.name
#   pattern        = "master"
#
#   require_pull_request_reviews = true
#   required_approving_review_count = 1
#
#   require_status_checks = true
#   strict = true
#   status_check_contexts = ["terraform-ci"]
#
#   enforce_admins = false
#
#   allow_force_pushes = false
#   allow_deletions = false
# }
