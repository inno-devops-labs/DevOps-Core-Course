# Yandex Cloud configuration
variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "service_account_key_file" {
  description = "Path to service account key file (JSON)"
  type        = string
  default     = "~/.config/yandex-cloud/key.json"
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

# VM configuration
variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "lab04-vm"
}

# SSH configuration
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
  description = "CIDR allowed to SSH, e.g. 203.0.113.10/32"
  type        = string
}

# GitHub configuration (for bonus task)
variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_owner" {
  description = "GitHub repository owner (username or organization)"
  type        = string
  default     = ""
}