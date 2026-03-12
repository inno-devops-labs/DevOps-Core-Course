output "repository_full_name" {
  description = "Full name of the imported GitHub repository"
  value       = github_repository.course_repo.full_name
}
