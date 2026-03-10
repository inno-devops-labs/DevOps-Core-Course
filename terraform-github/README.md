# Lab 04 Bonus - GitHub Repository Management with Terraform

## Overview

This configuration demonstrates importing and managing an existing GitHub repository using Terraform. This is a practical example of bringing existing infrastructure under IaC management.

## Why Import Existing Resources?

### The Problem
In real-world scenarios, infrastructure often exists before IaC adoption:
- Resources created manually
- Legacy systems
- Resources created by other teams/tools

You can't just run `terraform apply` - the resources already exist!

### The Solution: terraform import

Import brings existing resources under Terraform management without destroying them.

**Benefits:**
1. **Version Control** - Track configuration changes in Git
2. **Consistency** - Prevent configuration drift
3. **Automation** - Changes go through code review
4. **Documentation** - Code serves as documentation
5. **Disaster Recovery** - Quickly recreate from code
6. **Compliance** - All changes auditable

## Prerequisites

### 1. GitHub Personal Access Token

Create a token with appropriate permissions:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `terraform-repo-management`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `admin:repo_hook` (if managing webhooks)
5. Click "Generate token"
6. **Copy the token** (shown only once!)

### 2. Repository Information

You need:
- Repository name: `DevOps-Core-Course`
- Owner: Your GitHub username
- Repository must already exist

## Setup

### 1. Configure Terraform

```bash
cd terraform-github/

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
github_token = "ghp_your_token_here"
EOF

# Initialize Terraform
terraform init
```

### 2. Import Existing Repository

**IMPORTANT:** Before running `terraform apply`, you must import the existing repository:

```bash
# Format: terraform import <resource_type>.<name> <github_repo_id>
terraform import github_repository.devops_course DevOps-Core-Course

# Or if repository is in an organization:
terraform import github_repository.devops_course organization/DevOps-Core-Course
```

**What happens during import:**
1. Terraform queries GitHub API for repository details
2. Downloads current configuration
3. Saves it to state file
4. Now Terraform "knows" about this repository

### 3. Verify Import

```bash
# Check state
terraform show

# Plan should show minimal or no changes
terraform plan
```

If `terraform plan` shows many changes, your Terraform config doesn't match reality. Update `main.tf` to match actual repository settings.

### 4. Apply Changes

```bash
# After import, you can manage the repository
terraform apply
```

## Import Process Step-by-Step

### Step 1: Write Configuration

```hcl
resource "github_repository" "devops_course" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments"
  visibility  = "public"
  # ... other settings
}
```

### Step 2: Import

```bash
$ terraform import github_repository.devops_course DevOps-Core-Course

Importing from ID "DevOps-Core-Course"...
github_repository.devops_course: Importing...
github_repository.devops_course: Import prepared!
  Prepared github_repository for import
github_repository.devops_course: Import complete!

Import successful!
```

### Step 3: Align Configuration

```bash
$ terraform plan

Terraform will perform the following actions:

  # github_repository.devops_course will be updated in-place
  ~ resource "github_repository" "devops_course" {
      ~ description = "Old description" -> "DevOps course lab assignments"
      ~ topics      = [
          + "terraform",
          + "iac",
        ]
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

Update your Terraform config until `terraform plan` shows no changes.

### Step 4: Manage with Terraform

Now all changes go through Terraform:

```bash
# Change description
# Edit main.tf: description = "New description"
terraform apply

# Add topics
# Edit main.tf: topics = ["devops", "kubernetes"]
terraform apply
```

## What This Configuration Manages

### Repository Settings
- Name, description, visibility
- Features (issues, wiki, projects)
- Merge strategies
- Branch deletion settings
- Security alerts
- Topics/tags

### Branch Protection (master)
- Require status checks
- Require pull request reviews
- Prevent force pushes
- Prevent deletions

## Benefits of Managing GitHub with Terraform

### 1. Consistency Across Repos
```hcl
locals {
  standard_repo_config = {
    has_issues             = true
    has_wiki               = false
    delete_branch_on_merge = true
    vulnerability_alerts   = true
  }
}

resource "github_repository" "repo1" {
  name = "repo1"
  # Apply standard config
  dynamic "..." { for_each = local.standard_repo_config }
}
```

### 2. Team Management
```hcl
resource "github_team" "devops" {
  name = "devops-team"
}

resource "github_team_repository" "devops_access" {
  team_id    = github_team.devops.id
  repository = github_repository.devops_course.name
  permission = "maintain"
}
```

### 3. Branch Protection Rules
```hcl
resource "github_branch_protection" "main" {
  repository_id = github_repository.devops_course.node_id
  pattern       = "main"
  
  required_pull_request_reviews {
    required_approving_review_count = 2
  }
  
  required_status_checks {
    contexts = ["CI", "tests"]
  }
}
```

### 4. Webhooks
```hcl
resource "github_repository_webhook" "ci_webhook" {
  repository = github_repository.devops_course.name
  
  configuration {
    url          = "https://ci.example.com/webhook"
    content_type = "json"
  }
  
  events = ["push", "pull_request"]
}
```

## Import Other GitHub Resources

### Import a Team
```bash
terraform import github_team.devops 1234567
```

### Import Branch Protection
```bash
terraform import github_branch_protection.master DevOps-Core-Course:master
```

### Import Team Repository Access
```bash
terraform import github_team_repository.access 1234567:DevOps-Core-Course
```

## Real-World Use Cases

### 1. Organization-Wide Standards
**Problem:** 100+ repositories with inconsistent settings

**Solution:**
```hcl
# Apply to all repos
module "repository" {
  source = "./modules/standard-repo"
  
  for_each = toset([
    "repo1",
    "repo2",
    "repo3",
  ])
  
  name = each.key
}
```

### 2. Compliance Requirements
**Problem:** Need to enforce security policies

**Solution:**
```hcl
resource "github_repository" "compliant" {
  vulnerability_alerts = true
  
  # Require 2FA for collaborators
  # Require signed commits
  # etc.
}
```

### 3. Disaster Recovery
**Problem:** Accidentally deleted repository settings

**Solution:**
```bash
# Recreate from code
terraform apply
```

### 4. Multi-Repository Management
**Problem:** Maintaining 50+ similar repos

**Solution:** One Terraform config manages all

## Limitations and Considerations

### What Can't Be Managed?
- ❌ Repository content (code files)
- ❌ Issues and pull requests
- ❌ Commit history
- ❌ GitHub Actions secrets (use separate provider)

### Best Practices

**1. Separate State per Org/Team**
```bash
# Don't manage all repos in one state
terraform workspace new team-a
terraform workspace new team-b
```

**2. Use Modules for Common Patterns**
```hcl
module "standard_repo" {
  source = "./modules/repo"
  name   = "my-repo"
}
```

**3. Protect Terraform State**
- Use remote backend
- Encrypt state (contains tokens)
- Restrict access

**4. Plan Before Apply**
```bash
# Always review changes
terraform plan
# Especially for:
# - Branch protection changes
# - Permission changes
# - Deletion operations
```

## Troubleshooting

### Import Fails
```bash
Error: Cannot import non-existent resource
```
**Solution:** Check repository name and owner are correct.

### Plan Shows Many Changes After Import
**Solution:** Terraform config doesn't match reality. Update config to match current settings.

### Token Permissions Insufficient
```bash
Error: 403 Forbidden
```
**Solution:** Regenerate token with correct scopes (`repo`, `admin:repo_hook`).

### Resource Already Managed
```bash
Error: Resource already exists in state
```
**Solution:** Remove from state first:
```bash
terraform state rm github_repository.devops_course
```

## Security Best Practices

### 1. Token Management
```bash
# Use environment variable
export GITHUB_TOKEN="ghp_..."
terraform plan

# Or use terraform.tfvars (in .gitignore)
echo "github_token = \"ghp_...\"" > terraform.tfvars
```

### 2. Never Commit Tokens
```gitignore
# .gitignore
terraform.tfvars
*.tfvars
!terraform.tfvars.example
```

### 3. Use Least Privilege
- Create token with minimal required scopes
- Rotate tokens regularly
- Use different tokens for different purposes

### 4. Audit Trail
- All changes tracked in Git
- Terraform plan shows who changed what
- GitHub audit log for token usage

## Key Learnings

### 1. Import is Powerful
- Bring existing resources under IaC
- No downtime
- Gradual migration

### 2. Configuration Drift is Real
- Manual changes bypass Terraform
- Regularly run `terraform plan` to detect drift
- Enforce "Terraform-only" policy

### 3. State is Critical
- State maps config to reality
- Protect state file
- Use remote backend

### 4. Start Small
- Import one resource at a time
- Test thoroughly
- Expand gradually

## References

- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Terraform Import Command](https://www.terraform.io/cli/import)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Managing GitHub with Terraform](https://www.hashicorp.com/blog/managing-github-with-terraform)
