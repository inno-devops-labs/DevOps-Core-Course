variable "github_token" {
  description = "GitHub token with repo permissions"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub owner/user name"
  type        = string
  default     = "Linktur"
}

variable "repository_name" {
  description = "Repository name to import"
  type        = string
  default     = "DevOps-Core-Course"
}

variable "repository_description" {
  description = "Managed repository description"
  type        = string
  default     = "DevOps course lab assignments"
}
