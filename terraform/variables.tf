variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "AWS availability zone"
  type        = string
  default     = "us-east-1a"
}

variable "instance_type" {
  description = "EC2 instance type (free tier)"
  type        = string
  default     = "t2.micro"
}

variable "ssh_public_key" {
  description = "SSH public key"
  type        = string
  sensitive   = true
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH (your IP)"
  type        = string
}
