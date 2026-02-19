# GitHub Repository Management with Terraform

This directory contains Terraform configuration to manage your GitHub repository using Infrastructure as Code.

## Why Manage GitHub Repos with Terraform?

Managing GitHub repositories with Terraform provides several benefits:

1. **Version Control**: Track configuration changes over time
2. **Documentation**: Repository settings are visible in code
3. **Automation**: Changes require code review and testing
4. **Consistency**: Standardize settings across multiple repos
5. **Disaster Recovery**: Quickly recreate if needed
6. **Import Existing**: Bring existing repos under management

## Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set these scopes:
   - `repo` (Full control of private repositories)
   - `public_repo` (if repo is public)
   - `admin:org` (if using organization repos)
4. Generate and copy the token (you won't see it again!)

### 2. Configure Terraform

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with:
# - Your GitHub username
# - Repository name (exact name)
# - Your GitHub token
```

### 3. Import Existing Repository

To bring your existing repository under Terraform management:

```bash
# Initialize Terraform
terraform init

# Import the existing repository
# Format: terraform import github_repository.course_repo <repo_name>
terraform import github_repository.course_repo DevOps

# Review what Terraform found
terraform show

# Check for any differences
terraform plan
```

### 4. Update Configuration

After import, `terraform plan` may show differences between your code and the actual repository. Update `main.tf` to match reality:

```hcl
resource "github_repository" "course_repo" {
  name        = "DevOps"  # Exact name
  description = "Your actual description"  # Update if needed
  visibility  = "public"  # or "private"

  # Match actual settings...
}
```

Run `terraform plan` until it shows "No changes."

### 5. Apply Changes

Once configuration matches reality:

```bash
terraform apply
```

Now you can manage the repository with Terraform!

## Making Changes

Change settings in `main.tf`, then:

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

## Cleanup (Optional)

To remove from Terraform management (doesn't delete repo):

```bash
terraform state rm github_repository.course_repo
```

## Import Process Details

The import command links existing resources to Terraform:

1. **Before Import**: Repository exists, Terraform doesn't know about it
2. **Run Import**: `terraform import github_repository.course_repo DevOps`
3. **After Import**: Terraform tracks repository in state file
4. **Review**: `terraform plan` shows differences between code and reality
5. **Align**: Update code to match reality
6. **Verify**: `terraform plan` shows "No changes"
7. **Done**: Repository now managed as code

## Resources

- [GitHub Terraform Provider](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Terraform Import](https://developer.hashicorp.com/terraform/cli/import)
