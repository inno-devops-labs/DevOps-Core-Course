variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "zone" {
  description = "Zone"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_name" {
  description = "VM name"
  type        = string
  default     = "terraform-vm"
}

variable "image_id" {
  description = "Ubuntu image ID"
  type        = string
}

variable "ssh_user" {
  description = "SSH user"
  type        = string
  default     = "ubuntu"
}

variable "public_key_path" {
  description = "Path to SSH public key"
  type        = string
}
