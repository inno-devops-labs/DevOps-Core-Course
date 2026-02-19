variable "region" {
  description = "The AWS region to create resources in."
  default     = "us-east-1"
}

variable "instance_type" {
  description = "The type of EC2 instance to launch."
  default     = "t2.micro"
}

variable "github_token" {
  description = "The GitHub token to use for authentication."
  sensitive   = true
}
