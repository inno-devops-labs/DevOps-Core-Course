output "repositories" {
  value = [
    {
      name                   = github_repository.repo.name
      description            = github_repository.repo.description
      branch_protection_rule = github_branch_protection.repo_protection.id
      default_branch         = github_branch_default.repo_main.branch
      visibility             = github_repository.repo.visibility
    },
  ]
}
