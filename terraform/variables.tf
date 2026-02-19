variable "folder_id" {
  description = "ID folder for Yandex Cloud"
  type        = string
}

variable "zone" {
  description = "Zone Yandex Cloud"
  type        = string
  default     = "ru-central1-a"
}

variable "ssh_public_key" {
  description = "SSH public key for access to VM"
  type        = string
}
