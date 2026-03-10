terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# GitHub provider configuration
# Authentication via environment variable:
#   export GITHUB_TOKEN="your-personal-access-token"
# Or via terraform.tfvars (gitignored!):
#   token = "your-personal-access-token"
provider "github" {
  # Token is read from GITHUB_TOKEN environment variable automatically
  # Or can be set via: provider "github" { token = var.github_token }
}
