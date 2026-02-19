


provider "github" {
  token = var.github_token
}

resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false
}
