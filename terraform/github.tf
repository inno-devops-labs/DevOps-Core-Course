provider "github" {
  token = var.github_token
}

# Control creation via variable; default false to avoid accidental repo creation
resource "github_repository" "course_repo" {
  count       = var.create_github ? 1 : 0
  name        = "DevOps-Core-Course"
  description = "Course repo managed via Terraform (example)"
  visibility  = "public"
  has_issues  = true
  has_wiki    = false
}

variable "github_token" {
  description = "GitHub personal access token (set via env or terraform.tfvars)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "create_github" {
  description = "Whether to create GitHub repository via Terraform"
  type        = bool
  default     = false
}
