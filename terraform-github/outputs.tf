output "repo_full_name" {
  description = "Full name of the repository (owner/name)"
  value       = github_repository.course_repo.full_name
}

output "repo_html_url" {
  description = "URL of the repository"
  value       = github_repository.course_repo.html_url
}
