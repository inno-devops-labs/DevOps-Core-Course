# GitHub Repository Management with Terraform

This Terraform configuration manages the DevOps-Core-Course GitHub repository settings through Infrastructure as Code.

## Purpose

Demonstrates **terraform import** — bringing existing manually-created infrastructure under Terraform management (brownfield IaC adoption).

## What's Managed

- Repository metadata (name, description, visibility)
- Feature flags (issues, wiki, projects)
- Merge settings (merge commit, squash, rebase)
- Branch protection (optional, can be added)

## Setup

1. **Create GitHub Personal Access Token:**
   - Go to: Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope (full control of private repositories)
   - Copy token (shown once!)

2. **Configure authentication:**
   ```bash
   export GITHUB_TOKEN="your-token-here"
   export TF_VAR_github_owner="your-github-username"
   ```

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

## Usage

### View current state
```bash
terraform plan
```

### Apply changes
```bash
terraform apply
```

### Import existing repository (already done)
```bash
terraform import github_repository.course_repo DevOps-Core-Course
```

## Import Process Notes

The repository was imported with:
```bash
terraform import github_repository.course_repo DevOps-Core-Course
```

After import, configuration was updated to match actual GitHub state to prevent unwanted changes.

## Security

- Never commit `terraform.tfvars` with tokens
- Use environment variables or encrypted secrets
- `.gitignore` excludes sensitive files
- State file is gitignored (contains repo metadata)

## Resources

- [GitHub Provider Docs](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Import Guide](https://developer.hashicorp.com/terraform/cli/import)
