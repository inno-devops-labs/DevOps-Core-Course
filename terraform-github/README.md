# Terraform — GitHub Repository Import (Bonus Part 2)

Manages the DevOps-Core-Course GitHub repository via Terraform.

## Prerequisites

- Terraform >= 1.9
- GitHub Personal Access Token with `repo` scope

## Setup

1. Create `terraform.tfvars` in this directory (gitignored) with `github_token = "ghp_..."`.
2. Run from this directory:
   ```bash
   terraform init
   terraform import github_repository.course_repo DevOps-Core-Course
   terraform plan
   ```
   If the repo is under an organization: `terraform import github_repository.course_repo org/DevOps-Core-Course`.
3. If plan shows drift: align `main.tf` with current repo settings (for forks, GitHub may return 403 on apply; keeping config in sync with reality avoids apply).

## Resources Managed

Name, description, visibility, has_issues, has_wiki, has_projects, merge options, delete_branch_on_merge.

## Why Import Matters

Importing existing resources into Terraform gives version-controlled, reviewable changes instead of manual edits: audit trail, less configuration drift, disaster recovery from code.

## Benefits of Managing Repos with IaC

- Changes go through code review and CI.
- Single source of truth; no “who changed what” guesswork.
- Easy to replicate settings for new repos or restore after mistakes.
