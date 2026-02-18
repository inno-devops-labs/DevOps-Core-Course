variable "project_name" {
  description = "Name of the project, used for resource naming"
  type        = string
  default     = "lab04-devops"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "cloud_id" {
  description = "Yandex Cloud ID (optional if set via YC_CLOUD_ID env var)"
  type        = string
  default     = ""
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID (optional if set via YC_FOLDER_ID env var)"
  type        = string
  default     = ""
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
