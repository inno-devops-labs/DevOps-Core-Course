variable "folder_id" {
  description = "Yandex folder ID"
  type        = string
}

variable "zone" {
  description = "Availability zone"
  default     = "ru-central1-a"
}

variable "sa_key_path" {
  description = "Path to service account JSON key"
  type        = string
}
