# Repository Information
output "repository_name" {
  description = "Name of the GitHub repository"
  value       = github_repository.devops_course.name
}

output "repository_full_name" {
  description = "Full name of the repository (owner/repo)"
  value       = github_repository.devops_course.full_name
}

output "repository_url" {
  description = "URL of the GitHub repository"
  value       = github_repository.devops_course.html_url
}

output "repository_git_clone_url" {
  description = "Git clone URL"
  value       = github_repository.devops_course.git_clone_url
}

output "repository_ssh_clone_url" {
  description = "SSH clone URL"
  value       = github_repository.devops_course.ssh_clone_url
}

output "repository_topics" {
  description = "Topics assigned to the repository"
  value       = github_repository.devops_course.topics
}
