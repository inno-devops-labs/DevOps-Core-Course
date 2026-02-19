variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "myapp"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  sensitive   = true
}

variable "my_ip" {
  description = "Owner IP address"
  type        = string
  sensitive   = true
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
  sensitive   = true
}

# VM Configuration
variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_cores" {
  description = "Number of CPU cores for VM"
  type        = number
  default     = 2
}

variable "vm_memory" {
  description = "RAM size in GB for VM"
  type        = number
  default     = 1
}

variable "vm_core_fraction" {
  description = "Core fraction (5, 20, 50, 100)"
  type        = number
  default     = 20
}

variable "disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}

variable "image_id" {
  description = "Image ID for the VM"
  type        = string
  default     = "fd84mnbiarffhtfrhnog"  # Ubuntu 24.04 LTS
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "192.168.10.0/24"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
