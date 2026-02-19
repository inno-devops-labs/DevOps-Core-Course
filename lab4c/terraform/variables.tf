variable "yandex_folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "yandex_zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key file"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR allowed for SSH"
  type        = string
}

variable "yandex_service_account_key_file" {
  description = "Path to Yandex service account JSON key"
  type        = string
  default     = null
}
