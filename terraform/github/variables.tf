variable "github_token" {
  description = "GitHub Personal Access Token with repo scope"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
  default     = ""
}
