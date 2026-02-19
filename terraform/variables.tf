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

variable "ssh_public_key" {
  description = "The SSH public key to use for the deployer key pair. You should override this with your own public key in a terraform.tfvars file."
  type        = string
}
