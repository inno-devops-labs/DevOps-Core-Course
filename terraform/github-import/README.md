# GitHub Repository Import

This directory contains Terraform configuration for importing and managing the existing GitHub repository.

## Setup

1. **Create GitHub Personal Access Token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope
   - Copy token (shown only once!)

2. **Configure Authentication**
   ```bash
   export GITHUB_TOKEN="your-token-here"
   ```

3. **Import Existing Repository**
   ```bash
   cd terraform/github-import
   terraform init
   terraform import github_repository.course_repo DevOps-Core-Course
   ```

4. **Verify State Matches Reality**
   ```bash
   terraform plan
   # Should show "No changes" if config matches reality
   ```

5. **Update Config if Needed**
   - If `terraform plan` shows differences, update `main.tf` to match reality
   - Run `terraform plan` again until it shows "No changes"

6. **Apply Changes**
   ```bash
   terraform apply
   ```

## Why Import Existing Resources?

- **Version Control:** Track repository settings changes over time
- **Consistency:** Prevent configuration drift
- **Automation:** Changes require code review
- **Documentation:** Code is living documentation
- **Disaster Recovery:** Recreate repository settings from code

## What Can Be Managed?

- Repository settings (description, visibility, features)
- Branch protection rules
- Collaborators and teams
- Webhooks
- Repository secrets
- Deploy keys
