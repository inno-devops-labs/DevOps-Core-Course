##############################################
# GitHub Provider — Import existing repository
##############################################

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# -----------------------------------------------
# Provider
# -----------------------------------------------
provider "github" {
  token = var.github_token
}

# -----------------------------------------------
# Variables
# -----------------------------------------------
variable "github_token" {
  description = "GitHub Personal Access Token with repo scope"
  type        = string
  sensitive   = true
}

variable "repo_name" {
  description = "Name of the GitHub repository to manage"
  type        = string
  default     = "DevOps-Core-Course"
}

variable "repo_description" {
  description = "Repository description"
  type        = string
  default     = "DevOps core course — lab assignments"
}

variable "repo_visibility" {
  description = "Repository visibility (public or private)"
  type        = string
  default     = "public"
}

# -----------------------------------------------
# Imported repository resource
# -----------------------------------------------
resource "github_repository" "course_repo" {
  name        = var.repo_name
  description = var.repo_description
  visibility  = var.repo_visibility

  has_issues   = true
  has_wiki     = false
  has_projects = false

  # Prevent Terraform from trying to delete the repo on destroy
  archive_on_destroy = true
}

# -----------------------------------------------
# Outputs
# -----------------------------------------------
output "repo_full_name" {
  description = "Full name of the repository (owner/name)"
  value       = github_repository.course_repo.full_name
}

output "repo_html_url" {
  description = "URL of the repository"
  value       = github_repository.course_repo.html_url
}
