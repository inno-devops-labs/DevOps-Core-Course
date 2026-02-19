variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "devops-lab4"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "ssh_user" {
  description = "SSH username for VM access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (restrict to your IP)"
  type        = string
  # Default allows from anywhere - CHANGE THIS to your IP!
  # Example: "1.2.3.4/32" for single IP
  default = "0.0.0.0/0"
}

# Yandex auth (from env or terraform.tfvars; do not commit secrets)
variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  default     = ""
}

variable "yandex_folder_id" {
  description = "Yandex Folder ID"
  type        = string
  default     = ""
}

variable "yandex_service_account_key_file" {
  description = "Path to Yandex service account JSON key"
  type        = string
  default     = ""
  sensitive   = true
}
