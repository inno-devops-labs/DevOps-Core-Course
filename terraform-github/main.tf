terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
  required_version = ">= 1.9.0"
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

resource "github_repository" "course_repo" {
  name        = var.repository_name
  description = "DevOps Core Course - Infrastructure as Code Labs"
  visibility  = "public"

  has_issues      = true
  has_discussions = false
  has_projects    = false
  has_wiki        = false
  has_downloads   = true

  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = true
  allow_auto_merge       = false
  delete_branch_on_merge = true

  vulnerability_alerts = true

  topics = [
    "devops",
    "infrastructure-as-code",
    "terraform",
    "pulumi",
    "docker",
    "ci-cd",
    "ansible"
  ]
}

# Optional: Branch protection for main branch
resource "github_branch_protection" "main" {
  repository_id = github_repository.course_repo.node_id
  pattern       = "main"

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = false
    required_approving_review_count = 0
  }

  allows_deletions    = false
  allows_force_pushes = false
}
