# GitHub Provider Configuration (Bonus Task)
# This file demonstrates how to manage your GitHub repository with Terraform
# including importing existing resources and managing settings

#################################################################################
# SETUP INSTRUCTIONS:
#################################################################################
#
# 1. Create a GitHub Personal Access Token:
#    - Go to GitHub.com → Settings → Developer Settings → Personal Access Tokens
#    - Click "Generate new token (classic)"
#    - Select scopes: admin:repo, admin:org, notifications
#    - Copy the token (save it carefully!)
#
# 2. Set the token as an environment variable:
#    export GITHUB_TOKEN=ghp_xxxxx...
#    OR
#    Create a terraform.tfvars with: github_token = "ghp_xxxxx..."
#
# 3. Import the existing repository:
#    terraform import github_repository.course_repo DevOps-Core-Course
#
# 4. The existing GitHub repository will now be managed by Terraform
#
# 5. To apply changes to repository settings:
#    terraform plan
#    terraform apply
#
#################################################################################

terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  # Token from environment variable GITHUB_TOKEN
  # or from github_token variable below
  token = var.github_token

  # Your GitHub username/organization
  owner = var.github_owner
}

variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
  # Set via environment variable: GITHUB_TOKEN
  # Or via terraform.tfvars (add to .gitignore!)
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
  default     = "your-github-username"
}

#################################################################################
# IMPORT EXISTING REPOSITORY
#################################################################################
# 
# First, run this command to import your existing repository:
# terraform import github_repository.course_repo DevOps-Core-Course
#
# This will link your existing repository to the Terraform resource below.
#

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps Core Course - Infrastructure as Code Labs"
  
  # Visibility
  private = false
  
  # Features
  has_issues      = true      # Enable issues
  has_projects    = true      # Enable projects
  has_downloads   = true      # Enable downloads
  has_wiki        = false     # Disable wiki (optional)
  has_discussions = false     # Disable discussions (optional)
  
  # Repository settings
  is_template = false
  
  # Default branch
  default_branch = "master"
  
  # Topics/tags for discoverability
  topics = ["devops", "infrastructure-as-code", "terraform", "pulumi", "aws", "labs"]
  
  # Additional settings (optional)
  allow_auto_merge            = true     # Allow squash merges
  allow_merge_commit          = true
  allow_rebase_merge          = true
  allow_squash_merge          = true
  allow_update_branch         = true     # Allow branch updates
  delete_branch_on_merge      = true     # Auto-delete merged branches
  
  # License
  # license_template = "mit"  # Optional: add MIT license
  
  # Gitignore
  # gitignore_template = "Python"  # Optional: add gitignore
  
  tags = {
    "course"    = "DevOps"
    "module"    = "Lab04"
    "iac-tools" = "Terraform,Pulumi"
  }
}

#################################################################################
# OPTIONAL: Branch Protection
#################################################################################
#
# Requires admin access to repository
# Uncomment to enable branch protection rules
#

# resource "github_branch_protection" "main" {
#   repository_id          = github_repository.course_repo.node_id
#   pattern                = "main"
#   enforce_admins         = false
#   require_conversation_resolution = false
#   
#   required_status_checks {
#     strict   = true
#     contexts = ["Terraform Validation"]
#   }
#   
#   required_pull_request_reviews {
#     dismiss_stale_reviews      = true
#     require_code_owner_reviews = false
#     required_approving_review_count = 1
#   }
# }

#################################################################################
# OPTIONAL: Collaborative Settings
#################################################################################
#
# Uncomment to add collaborators/teams
#

# resource "github_repository_collaborator" "ta" {
#   repository = github_repository.course_repo.name
#   username   = "ta-username"
#   permission = "maintain"  # pull, triage, push, admin, maintain
# }

#################################################################################
# OUTPUTS
#################################################################################

output "repository_url" {
  description = "HTTPS URL of the repository"
  value       = github_repository.course_repo.html_url
}

output "repository_clone_https" {
  description = "Clone URL (HTTPS)"
  value       = github_repository.course_repo.clone_set[0].https_url
}

output "repository_clone_ssh" {
  description = "Clone URL (SSH)"
  value       = github_repository.course_repo.clone_set[0].ssh_url
}

output "repository_full_name" {
  description = "Full name (owner/repo)"
  value       = github_repository.course_repo.full_name
}

output "repository_topics" {
  description = "Repository topics/tags"
  value       = github_repository.course_repo.topics
}

#################################################################################
# WHY IMPORT EXISTING RESOURCES?
#################################################################################
#
# Benefits of managing existing infrastructure with Terraform:
#
# 1. VERSION CONTROL
#    - All configuration changes tracked in Git
#    - History of who changed what and when
#    - Can revert bad changes
#
# 2. COMPLIANCE & GOVERNANCE
#    - Enforce security policies
#    - Ensure consistent configuration
#    - Audit trail of changes
#
# 3. COLLABORATION
#    - Team reviews infrastructure changes via PRs
#    - Prevents manual, undocumented changes
#    - Single source of truth
#
# 4. DISASTER RECOVERY
#    - Configuration can be quickly reapplied
#    - No manual steps to remember
#    - Tested backup/restore process
#
# 5. DOCUMENTATION
#    - Code serves as living documentation
#    - Everyone sees current configuration
#    - No "tribal knowledge" needed
#
# EXAMPLES OF WHAT TO MANAGE:
#
# ✓ Repository settings (description, topics, visibility)
# ✓ Branch protection rules (required reviews, status checks)
# ✓ Collaborators and team access
# ✓ Repository labels
# ✓ Webhooks and integrations
# ✓ Deploy keys
# ✓ Pull request automation rules
#
#################################################################################

#################################################################################
# COMMON TASKS
#################################################################################
#
# ADD A COLLABORATOR:
# 
# resource "github_repository_collaborator" "collaborator" {
#   repository = github_repository.course_repo.name
#   username   = "collaborator-username"
#   permission = "push"  # pull, triage, push, maintain, admin
# }
#
# ADD BRANCH PROTECTION:
#
# resource "github_branch_protection" "master" {
#   repository_id = github_repository.course_repo.node_id
#   pattern       = "master"
#   
#   required_status_checks {
#     strict   = true
#     contexts = ["GitHub Actions CI/CD"]
#   }
# }
#
# CREATE ISSUE LABELS:
#
# resource "github_issue_label" "bug" {
#   repository = github_repository.course_repo.name
#   name       = "bug"
#   color      = "d73a4a"
#   description = "Bug report"
# }
#
# ADD WEBHOOK:
#
# resource "github_repository_webhook" "cicd" {
#   repository = github_repository.course_repo.name
#   events     = ["push", "pull_request"]
#   
#   configuration {
#     url          = "https://example.com/webhook"
#     content_type = "json"
#     insecure_ssl = false
#   }
#
#################################################################################
