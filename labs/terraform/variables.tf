variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
}

variable "repo_name" {
  description = "Course repository name"
  type        = string
}

variable "repo_description" {
  description = "Repository description managed by Terraform"
  type        = string
  default     = "DevOps Core Course repository (managed by Terraform)"
}

variable "repo_visibility" {
  description = "Repository visibility"
  type        = string
  default     = "public"
}