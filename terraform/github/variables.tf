variable "github_token" {
  type      = string
  sensitive = true
}

variable "github_owner" {
  type = string
}

variable "repo_name" {
  type    = string
  default = "DevOps-Core-Course"
}