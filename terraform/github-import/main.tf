# GitHub Repository Resource
# This will be imported from existing repository
resource "github_repository" "course_repo" {
  name        = "DevOps-Core-Course"
  description = "DevOps course lab assignments and projects"
  visibility  = "public"

  has_issues    = true
  has_wiki      = false
  has_projects  = false
  has_downloads = true

  # Branch protection and other settings can be added here
  # See: https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository
}
