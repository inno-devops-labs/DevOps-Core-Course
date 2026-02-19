variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming and tags"
  type        = string
  default     = "devops-lab04"
}

variable "instance_type" {
  description = "EC2 instance type (use t2.micro for free tier)"
  type        = string
  default     = "t2.micro"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key for VM access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH (restrict to your IP for security)"
  type        = string
  default     = "0.0.0.0/0" # Replace with your IP/32 in production
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project = "DevOps-Core-Course"
    Lab     = "lab04"
  }
}
