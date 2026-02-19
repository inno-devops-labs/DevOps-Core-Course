# Cloud configuration
variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "zone" {
  description = "Availability zone"
  type        = string
  default     = "ru-central1-a"
}

# VM configuration
variable "vm_name" {
  description = "VM name"
  type        = string
  default     = "lab4-vm"
}

variable "vm_platform" {
  description = "Platform ID"
  type        = string
  default     = "standard-v2" # Modern Intel Cascade Lake
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_memory" {
  description = "Memory in GB"
  type        = number
  default     = 1
}

variable "vm_core_fraction" {
  description = "CPU performance level (5, 20, 50, 100)"
  type        = number
  default     = 20 # 20% for free tier
}

variable "disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "image_family" {
  description = "Image family"
  type        = string
  default     = "ubuntu-2404-lts-oslogin" # Ubuntu 24.04 LTS
}

# Network configuration
variable "v4_cidr_blocks" {
  description = "CIDR blocks for subnet"
  type        = list(string)
  default     = ["10.10.0.0/24"]
}

variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "lab4-network"
}

variable "subnet_name" {
  description = "Subnet name"
  type        = string
  default     = "lab4-subnet"
}

# Security
variable "ssh_public_key" {
  description = "SSH public key"
  type        = string
  sensitive   = true
}

# Allowed IPs for SSH (restrict to your IP for security)
variable "allowed_ssh_ips" {
  description = "IPs allowed to connect via SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change to your IP for production!
}

# Tags
variable "labels" {
  description = "Resource labels"
  type        = map(string)
  default = {
    environment = "lab"
    project     = "devops-course"
    managed_by  = "terraform"
  }
}
