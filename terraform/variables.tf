variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "lab06"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type (free tier)"
  type        = string
  default     = "t2.micro"
}

variable "my_ip_address" {
  description = "Your IP address for SSH access (e.g., 1.2.3.4/32)"
  type        = string
  sensitive   = true
}

variable "key_name" {
  description = "Name of the existing key pair in AWS"
  type        = string
  default     = "labsuser"
}
