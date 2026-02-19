variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "devops-lab04"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "zone" {
  description = "Yandex Cloud zone (e.g., ru-central1-a)"
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access (restrict to your IP)"
  type        = string
  # Default allows from anywhere - CHANGE THIS to your IP!
  # Example: "1.2.3.4/32" for single IP
  default     = "0.0.0.0/0"
}

variable "ssh_username" {
  description = "SSH username for VM access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "folder_id" {
  description = "Yandex Cloud folder ID (optional, can be set via YC_FOLDER_ID env var)"
  type        = string
  default     = ""
}
