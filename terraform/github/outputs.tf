output "repository_name" {
  description = "Repository name"
  value       = github_repository.course_repo.name
}

output "repository_url" {
  description = "Repository URL"
  value       = github_repository.course_repo.html_url
}

output "repository_ssh_clone" {
  description = "SSH clone URL"
  value       = github_repository.course_repo.ssh_clone_url
}

output "repository_http_clone" {
  description = "HTTP clone URL"
  value       = github_repository.course_repo.http_clone_url
}

output "has_issues" {
  description = "Issues enabled"
  value       = github_repository.course_repo.has_issues
}

output "visibility" {
  description = "Repository visibility"
  value       = github_repository.course_repo.visibility
}
