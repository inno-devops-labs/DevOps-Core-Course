variable "yc_service_account_key_file" {
  description = "Path to Yandex Cloud service account key JSON file"
  type        = string
  default     = ""
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  default     = ""
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
  default     = ""
}

variable "yc_zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_user" {
  description = "Username for the VM"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key" {
  description = "SSH public key content for VM access"
  type        = string
  default     = ""
}
