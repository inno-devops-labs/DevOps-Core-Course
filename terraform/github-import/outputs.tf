output "repository_name" {
  description = "Name of the GitHub repository"
  value       = github_repository.course_repo.name
}

output "repository_url" {
  description = "URL of the GitHub repository"
  value       = github_repository.course_repo.html_url
}

output "repository_id" {
  description = "ID of the GitHub repository"
  value       = github_repository.course_repo.id
}
