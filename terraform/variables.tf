variable "yc_token" {
  description = "Yandex Cloud IAM token (get via: yc iam create-token)"
  type        = string
  sensitive   = true
}

variable "yc_folder_id" {
  description = "Yandex Cloud folder ID (required for free tier)"
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
  description = "Your public IP address in CIDR format (e.g., 95.123.45.67/32) for SSH access"
  type        = string
  validation {
    condition     = can(cidrhost(var.my_ip_cidr, 0))
    error_message = "Must be a valid CIDR block (e.g., 95.123.45.67/32). Get your IP: curl ifconfig.me"
  }
}

variable "ssh_public_key" {
  description = "SSH public key for VM access (content of ~/.ssh/id_rsa.pub)"
  type        = string
  sensitive   = true
}