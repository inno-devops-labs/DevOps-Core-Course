variable "project_name" {
  description = "Prefix for resource names"
  type        = string
  default     = "iac-lab4"
}

variable "zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "ru-central1-a"
}

variable "platform" {
  description = "Platform id for vm"
  type        = string
  default     = "standard-v2"
}



variable "yandex_service_account_key_file" {
  description = "Path to service account JSON key file"
  type        = string
  default     = "authorized-key.json"
}

variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yandex_folder_id" {
  description = "Yandex Cloud folder (catalog) ID"
  type        = string
}



variable "vpc_network_name" {
  description = "Name of existing VPC network to use (e.g. default)"
  type        = string
  default     = "default"
}



variable "ssh_public_key_path" {
  description = "Path to SSH public key file for VM access"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed for SSH (e.g. 0.0.0.0/0 or your IP/32)"
  type        = string
  default     = "0.0.0.0/0"
}
