variable "token" {
  description = "Yandex Cloud OAuth token"
  type        = string
  sensitive   = true
}

variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "ssh_user" {
  description = "SSH username for VM access"
  type        = string
  default     = "vglon"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "my_ip_cidr" {
  description = "Your IP address in CIDR format (e.g., 1.2.3.4/32) for SSH access"
  type        = string
}
