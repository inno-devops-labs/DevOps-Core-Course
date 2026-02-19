output "repository_url" {
  description = "Repository HTML URL"
  value       = github_repository.course_repo.html_url
}

output "repository_name" {
  description = "Repository name"
  value       = github_repository.course_repo.name
}

output "repository_full_name" {
  description = "Repository full name (owner/repo)"
  value       = github_repository.course_repo.full_name
}
