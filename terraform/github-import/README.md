# Terraform Bonus: GitHub Repository Import

## Setup
```bash
cd terraform/github-import
terraform init
```

Set token as environment variable:
```bash
export TF_VAR_github_token=ghp_xxx
```

## Import existing repository
```bash
terraform import github_repository.course_repo DevOps-Core-Course
terraform plan
```

## Apply managed settings
```bash
terraform apply
```

This keeps existing repository under Terraform control and lets you manage settings as code.
