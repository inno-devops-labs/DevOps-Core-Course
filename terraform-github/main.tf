terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
  required_version = ">= 1.0"
}

# Provider configuration
provider "github" {
  token = var.github_token
}

# Import existing GitHub repository
resource "github_repository" "devops_course" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments - Infrastructure as Code, CI/CD, Docker, Kubernetes"
  visibility  = "public"

  has_issues    = true
  has_wiki      = false
  has_projects  = false
  has_downloads = true

  # Enable features
  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = true
  allow_auto_merge       = false
  delete_branch_on_merge = true

  # Security
  vulnerability_alerts = true

  # Topics/Tags
  topics = [
    "devops",
    "terraform",
    "pulumi",
    "docker",
    "kubernetes",
    "ci-cd",
    "ansible",
    "infrastructure-as-code",
    "innopolis",
  ]
}

# Branch protection for master
resource "github_branch_protection" "master" {
  repository_id = github_repository.devops_course.node_id
  pattern       = "master"

  required_status_checks {
    strict   = false
    contexts = []
  }

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    required_approving_review_count = 0 # No approval required for personal repo
  }

  allows_deletions    = false
  allows_force_pushes = false
}
