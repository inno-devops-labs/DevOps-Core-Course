variable "ssh_pubkey_path" {
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
  sensitive   = true
}

variable "iam_token" {
  type        = string
  description = "Specifies IAM token for auth in Yandex Cloud"
  sensitive   = true
}

variable "zone" {
  type    = string
  default = "ru-central1-b"
}

variable "cloud_id" {
  type        = string
  description = "Cloud ID"
  sensitive   = true
}

variable "folder_id" {
  type        = string
  description = "Foder ID within the cloud"
  sensitive   = true
}

variable "vm_image_id" {
  type        = string
  description = "Base image for virtual machines"
  default     = "fd83s8u085j3mq231ago"
}

variable "vm_name" {
  type    = string
  default = "terraform-vm"
}

variable "ram_gb" {
  type    = number
  default = 2
}

variable "cpu_cores" {
  type    = number
  default = 2
}

variable "vm_username" {
  type      = string
  default   = "ubuntu"
  sensitive = true
}

