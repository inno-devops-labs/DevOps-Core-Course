# Managing GitHub Repository with Terraform

This directory demonstrates importing an existing GitHub repository into Terraform management.

## Why Import Existing Resources?

When adopting Infrastructure as Code, you often have existing resources that were created manually. The `terraform import` command allows you to bring these resources under Terraform management without recreating them.

**Benefits:**
- Track all infrastructure changes in version control
- Review changes before applying (via PR)
- Ensure consistency across resources
- Enable disaster recovery (recreate from code)
- Prevent unauthorized manual changes
- Document infrastructure as code

## Prerequisites

1. **Terraform CLI**: Already installed from main lab
2. **GitHub Account**: Your course repository already exists
3. **GitHub Personal Access Token**: Create with `repo` scope

## Setup Instructions

### 1. Create GitHub Personal Access Token

```bash
# Go to: https://github.com/settings/tokens/new
# Or: Settings → Developer settings → Personal access tokens → Tokens (classic)

# Token name: Terraform Lab 04
# Scopes: Select "repo" (all repository permissions)
# Generate token and copy it (shown only once!)
```

### 2. Configure Variables

```bash
cd terraform-github

# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
# - github_token: Your personal access token
# - github_owner: Your GitHub username
# - repository_name: DevOps-Core-Course (default)
```

### 3. Initialize Terraform

```bash
terraform init
terraform fmt
terraform validate
```

### 4. Import Existing Repository

**Important:** The repository already exists on GitHub. We need to import it first before managing it with Terraform.

```bash
# Format: terraform import <resource_type>.<name> <repository_name>
terraform import github_repository.course_repo DevOps-Core-Course

# This tells Terraform to track the existing repository
```

### 5. Verify Import

```bash
# Check if configuration matches reality
terraform plan

# If there are differences, you have two options:
# 1. Update main.tf to match the current repository settings
# 2. Apply changes to update repository to match main.tf

# After fixing differences
terraform plan
# Should show: "No changes. Infrastructure is up-to-date."
```

### 6. Make Changes (Optional)

```bash
# Edit main.tf to change repository settings
# For example, update description, topics, settings

# Preview changes
terraform plan

# Apply changes
terraform apply
```

## What Can You Manage?

With the GitHub provider, you can manage:

- **Repository settings**: description, visibility, features
- **Branch protection rules**: require reviews, status checks
- **Collaborators and teams**: access control
- **Webhooks**: automate workflows
- **Deploy keys**: SSH keys for deployments
- **Repository secrets**: CI/CD secrets (encrypted)
- **Topics and metadata**: categorization

## Import Process Explained

```
Before Import:
├── GitHub Repository (exists manually)
└── Terraform Config (describes what should exist)
    ❌ Terraform doesn't know about the real repository

After Import:
├── GitHub Repository (exists)
├── Terraform Config (describes repository)
└── Terraform State (tracks real repository)
    ✅ Terraform now manages the repository
```

## Files

- `main.tf`: Repository resource configuration
- `variables.tf`: Input variables
- `outputs.tf`: Repository information outputs
- `terraform.tfvars`: Variable values (gitignored)
- `terraform.tfvars.example`: Example configuration

## Import Command Explained

```bash
terraform import github_repository.course_repo DevOps-Core-Course
#              └─ resource_type.name            └─ actual repo name on GitHub
```

**What happens:**
1. Terraform queries GitHub API for repository "DevOps-Core-Course"
2. Downloads current repository configuration
3. Saves it to terraform.tfstate
4. Links the state to the resource in main.tf
5. Future `terraform apply` will update the repository

## Troubleshooting

**Authentication Failed:**
```bash
# Verify token is set correctly
# Check token has 'repo' scope
# Try setting as environment variable:
export GITHUB_TOKEN="your-token-here"
```

**Import Failed:**
```bash
# Check repository name is correct (case-sensitive)
# Verify you have access to the repository
# Check repository owner matches your username
```

**Plan Shows Differences After Import:**
- Normal! Imported state might not match your config
- Update main.tf to match reality
- Or apply to update repository to match config
- Goal: `terraform plan` shows no changes

## Security Notes

⚠️ **Never commit:**
- `terraform.tfvars` (contains GitHub token)
- `terraform.tfstate` (contains repository details)

✅ **Safe to commit:**
- `*.tf` files (configuration)
- `terraform.tfvars.example` (template)
- This README

## Real-World Use Case

**Scenario:** Your company has 100 GitHub repositories created manually over the years.

**Problem:**
- Settings are inconsistent
- No audit trail of changes
- Branch protection configured differently
- Manual changes cause security issues

**Solution with Terraform:**
1. Import all repositories: `terraform import ...`
2. Define standard configuration in code
3. Apply to standardize all repositories
4. All future changes go through PR review
5. Consistent, auditable, version-controlled

**Benefits:**
- Compliance: All repos follow security policies
- Audit: Track who changed what and when
- Recovery: Recreate repos from code if needed
- Collaboration: Team reviews changes via PR
- Automation: CI validates changes automatically

## Alternative: Pulumi

You can also manage GitHub resources with Pulumi:

```python
import pulumi
import pulumi_github as github

repo = github.Repository("course-repo",
    name="DevOps-Core-Course",
    description="DevOps course",
    visibility="public",
    has_issues=True)

pulumi.export("repo_url", repo.html_url)
```

## Cleanup

```bash
# WARNING: This will NOT delete the repository
# It only removes Terraform management
terraform destroy

# To keep managing with Terraform, don't destroy
```

## Next Steps

1. Import your course repository ✅
2. Verify settings match your config
3. Make a small change (e.g., update description)
4. Apply and verify on GitHub
5. Understand: Now all changes can be code-reviewed!

## Resources

- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Terraform Import Guide](https://developer.hashicorp.com/terraform/cli/import)

---

**Key Takeaway:** Infrastructure as Code isn't just for cloud resources. You can manage GitHub repositories, databases, monitoring alerts, DNS records, and much more. Anything with an API can be managed as code!
