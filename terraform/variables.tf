variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_key_file" {
  description = "Path to service account key JSON file"
  type        = string
  default     = "~/yc-key.json"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "image_id" {
  description = "Boot disk image ID (Ubuntu 24.04 LTS)"
  type        = string
  default     = "fd8p685sjqdraf7mpkuc"
}
