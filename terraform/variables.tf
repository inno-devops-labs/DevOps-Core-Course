variable "folder_id" {
  description = "Yandex Cloud folder id"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "instance_name" {
  description = "Name for the compute instance"
  type        = string
  default     = "lab4"
}

variable "ssh_public_key" {
  description = "Your SSH public key content"
  type        = string
  sensitive   = true
}

variable "service_account_key_file" {
  description = "Path to Yandex Cloud service account key JSON file"
  type        = string
  default     = "~/.config/yandex-cloud/sa-key.json"
}
