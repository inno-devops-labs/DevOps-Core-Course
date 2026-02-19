terraform {
  required_version = ">= 1.5.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "🚀Production-grade DevOps course: 18 hands-on labs covering Docker, Kubernetes, Helm, Terraform, Ansible, CI/CD, GitOps (ArgoCD), monitoring (Prometheus/Grafana), and more. Build real-world skills with progressive delivery, secrets management, and cloud-native deployments."
  visibility  = "public"

  has_issues   = false
  has_wiki     = true
  has_projects = true

  allow_merge_commit = false
  allow_squash_merge = false
  allow_rebase_merge = false

  delete_branch_on_merge = false
}
