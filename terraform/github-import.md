# GitHub Repository Import Guide

This guide explains how to import an existing GitHub repository into Terraform management.

## Why Import Existing Resources?

In real-world scenarios, you often have:
- Infrastructure created manually (before IaC adoption)
- Resources created by other tools or people
- Legacy systems that need to be managed with code

Importing brings existing resources under Terraform management, allowing you to:
- Track configuration changes over time
- Ensure consistency across resources
- Enable code review for infrastructure changes
- Automate infrastructure management
- Create disaster recovery plans

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` scope (all repository permissions)
   - Copy token (shown only once!)

2. **Set Token**
   ```bash
   export GITHUB_TOKEN=your-token-here
   # Or add to terraform.tfvars (gitignored!)
   ```

## Import Process

### Step 1: Write Resource Configuration

The resource configuration is already defined in `github-provider.tf`:

```hcl
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps Core Course - Lab assignments and projects"
  visibility  = "public"
  ...
}
```

### Step 2: Initialize Terraform

```bash
cd terraform
terraform init
```

This will download the GitHub provider.

### Step 3: Import Existing Repository

```bash
# Format: terraform import <resource_type>.<name> <repo_name>
terraform import github_repository.course_repo DevOps-Core-Course
```

**Expected Output:**
```
github_repository.course_repo: Importing from ID "DevOps-Core-Course"...
github_repository.course_repo: Import prepared!
  Prepared github_repository for import
github_repository.course_repo: Refreshing state... [id=...]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

### Step 4: Verify State Matches Reality

```bash
terraform plan
```

**Expected Output:**
```
No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

If there are differences, Terraform will show them. Update your configuration to match reality.

### Step 5: Apply Configuration

```bash
terraform apply
```

This ensures your configuration matches the repository settings.

## Managing Repository Settings

After import, you can manage repository settings via Terraform:

```bash
# Update description
terraform apply -var="github_repo_description=New description"

# Change visibility (if you have permissions)
terraform apply -var="github_repo_visibility=private"
```

## Benefits of Managing Repos with IaC

1. **Version Control**
   - Track all configuration changes in Git
   - See who changed what and when
   - Rollback to previous configurations

2. **Consistency**
   - Standardize repository settings across organization
   - Prevent configuration drift
   - Ensure compliance with policies

3. **Automation**
   - Changes require code review (PR workflow)
   - CI/CD validation
   - Automated testing

4. **Documentation**
   - Code is living documentation
   - Anyone can see current configuration
   - No "tribal knowledge" needed

5. **Disaster Recovery**
   - Quickly recreate repositories from code
   - No manual steps to remember
   - Tested recovery process

6. **Team Collaboration**
   - Multiple people can work on infrastructure
   - PR-based workflow
   - No conflicting manual changes

## Example: Import Output

```bash
$ terraform import github_repository.course_repo DevOps-Core-Course

github_repository.course_repo: Importing from ID "DevOps-Core-Course"...
github_repository.course_repo: Import prepared!
  Prepared github_repository for import
github_repository.course_repo: Refreshing state... [id=123456789]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.

$ terraform plan

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

## Cleanup

To remove the repository from Terraform management (but keep the repo):

```bash
terraform state rm github_repository.course_repo
```

To delete the repository entirely:

```bash
# First, set archive_on_destroy = false in github-provider.tf
terraform apply
terraform destroy
```

## Security Notes

- ⚠️ Never commit `GITHUB_TOKEN` to Git
- ✅ Use environment variables or GitHub Secrets
- ✅ Use `terraform.tfvars` (gitignored) for local development
- ✅ Rotate tokens regularly
- ✅ Use fine-grained tokens with minimal permissions when possible

## Resources

- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [Repository Resource](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository)
- [Import Guide](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository#import)
- [Terraform Import Command](https://developer.hashicorp.com/terraform/cli/import)
