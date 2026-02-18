variable "yc_token" {
  description = "Yandex Cloud IAM token"
  type        = string
  sensitive   = true
}

variable "yc_folder_id" {
  description = "Yandex folder id"
  type        = string
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "ru-central1"
}

variable "zone" {
  description = "Availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_name" {
  description = "VM instance name"
  type        = string
  default     = "free-tier-vm"
}

variable "my_ip_cidr" {
  description = "my public ip"
  type        = string
  validation {
    condition     = can(cidrhost(var.my_ip_cidr, 0))
    error_message = "Must be a valid CIDR block - Get your IP: curl ifconfig.me"
  }
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
  sensitive   = true
}
