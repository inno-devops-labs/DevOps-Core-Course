output "repository_url" {
  description = "URL of the GitHub repository"
  value       = github_repository.devops_course.html_url
}

output "repository_full_name" {
  description = "Full name of the GitHub repository (owner/name)"
  value       = github_repository.devops_course.full_name
}
