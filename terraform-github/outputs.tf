output "repository_url" {
  description = "URL of the GitHub repository"
  value       = github_repository.course_repo.html_url
}

output "repository_full_name" {
  description = "Full name of the repository (owner/name)"
  value       = github_repository.course_repo.full_name
}

output "repository_ssh_clone_url" {
  description = "SSH clone URL"
  value       = github_repository.course_repo.ssh_clone_url
}

output "repository_http_clone_url" {
  description = "HTTPS clone URL"
  value       = github_repository.course_repo.http_clone_url
}
