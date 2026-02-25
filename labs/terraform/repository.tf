resource "github_repository" "course" {
  name        = var.repo_name
  description = var.repo_description
  visibility  = var.repo_visibility

  has_issues = true
  has_wiki   = true

  # Important for import of an existing repo:
  # do not let Terraform try to initialize/reset repo content
  auto_init = false

  lifecycle {
    ignore_changes = [
      # Ignore fields that may differ in an existing repo initially
      homepage_url,
      topics,
    ]
  }
}