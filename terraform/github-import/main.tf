terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

# Authenticate via GITHUB_TOKEN environment variable (never hardcode!)
provider "github" {}

variable "repo_name" {
  description = "Name of the GitHub repository to import"
  type        = string
  default     = "DevOps-Core-Course"
}

# ── Repository resource ─────────────────────────────────────────────────────
# After writing this block, run:
#   export GITHUB_TOKEN="ghp_..."          # or $env:GITHUB_TOKEN = "ghp_..."
#   terraform init
#   terraform import github_repository.course_repo DevOps-Core-Course
#   terraform plan   # should show no changes if config matches reality
resource "github_repository" "course_repo" {
  name        = var.repo_name
  description = "DevOps course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false

  # Prevent Terraform from destroying the repo on `terraform destroy`
  lifecycle {
    prevent_destroy = true
  }
}

# ── Outputs ──────────────────────────────────────────────────────────────────
output "repo_full_name" {
  value = github_repository.course_repo.full_name
}

output "repo_html_url" {
  value = github_repository.course_repo.html_url
}
