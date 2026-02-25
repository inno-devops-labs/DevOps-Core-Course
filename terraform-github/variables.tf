variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
}

variable "repository_name" {
  description = "Name of the repository to manage"
  type        = string
  default     = "DevOps-Core-Course"
}
