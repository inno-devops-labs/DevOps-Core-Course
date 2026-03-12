variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Availability zone for the public subnet"
  type        = string
  default     = "us-east-1a"
}

variable "project_name" {
  description = "Project name used in tags"
  type        = string
  default     = "devops-core-lab04"
}

variable "instance_type" {
  description = "EC2 instance type (use free-tier type)"
  type        = string
  default     = "t2.micro"
}

variable "instance_username" {
  description = "SSH username for Ubuntu images"
  type        = string
  default     = "ubuntu"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.10.1.0/24"
}

variable "ssh_allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access SSH (use your IP/32)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ssh_public_key_path" {
  description = "Path to your public SSH key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "key_pair_name" {
  description = "AWS key pair name"
  type        = string
  default     = "devops-core-lab04-key"
}
