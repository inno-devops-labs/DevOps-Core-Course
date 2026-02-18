output "repository_url" {
  value = github_repository.course_repo.html_url
}

output "repository_name" {
  value = github_repository.course_repo.name
}

output "visibility" {
  value = github_repository.course_repo.visibility
}
