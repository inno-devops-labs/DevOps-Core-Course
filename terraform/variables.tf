# ============================================================
# Input Variables
# ============================================================

# ---------- Yandex Cloud credentials ----------

variable "yc_token" {
  description = "Yandex Cloud OAuth token or IAM token"
  type        = string
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "yc_zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "existing_network_id" {
  description = "Existing VPC network ID to reuse (optional). If empty, Terraform creates a new network"
  type        = string
  default     = ""
}

variable "existing_subnet_id" {
  description = "Existing subnet ID to reuse (optional). If empty, Terraform creates a new subnet"
  type        = string
  default     = ""
}

# ---------- VM settings ----------

variable "vm_user" {
  description = "Username for SSH access to the VM"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
