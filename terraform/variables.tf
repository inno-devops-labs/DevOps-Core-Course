variable "project_name" {
  description = "Name prefix for all resources."
  type        = string
  default     = "lab04"
}

variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (use smallest/free-tier if possible)."
  type        = string
  default     = "t2.micro"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_ingress_cidr" {
  description = "CIDR allowed to SSH (port 22). If null, uses your current public IP /32."
  type        = string
  default     = null
}

variable "allowed_http_cidr" {
  description = "CIDR allowed to HTTP (port 80)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "allowed_app_cidr" {
  description = "CIDR allowed to app port (5000)."
  type        = string
  default     = "0.0.0.0/0"
}

variable "key_name" {
  description = "AWS EC2 key pair name."
  type        = string
  default     = "lab04-key"
}

variable "public_key_path" {
  description = "Path to SSH public key to register in AWS."
  type        = string
  default     = "./keys/lab04_terraform_key.pub"
}
