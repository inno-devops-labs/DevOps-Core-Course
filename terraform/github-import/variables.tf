variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
  default     = null # Prefer environment variable GITHUB_TOKEN
}
