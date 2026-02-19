variable "cloud_id" {
  description = "Yandex Cloud ID"
}

variable "folder_id" {
  description = "Yandex Folder ID"
}

variable "zone" {
  default = "ru-central1-a"
}

variable "iam_token" {
  description = "IAM token"
  sensitive   = true
}

variable "ssh_user" {
  default = "ubuntu"
}

variable "ssh_public_key" {
  description = "SSH public key"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
}
