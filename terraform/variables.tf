# =============================================================================
# Yandex Cloud Provider Configuration
# =============================================================================

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

# =============================================================================
# VM Configuration
# =============================================================================

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "devops-vm"
}

variable "vm_platform_id" {
  description = "Platform ID for the VM (standard-v2 for Intel Cascade Lake)"
  type        = string
  default     = "standard-v2"
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_core_fraction" {
  description = "CPU core fraction (percentage of dedicated CPU time)"
  type        = number
  default     = 20
}

variable "vm_memory" {
  description = "Amount of RAM in GB"
  type        = number
  default     = 1
}

variable "vm_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "vm_disk_type" {
  description = "Boot disk type (network-hdd, network-ssd, network-ssd-nonreplicated)"
  type        = string
  default     = "network-hdd"
}

variable "vm_image_id" {
  description = "Image ID for the VM boot disk (Ubuntu 24.04 LTS)"
  type        = string
  default     = "fd8g5aftj139tv8u2mo1" # Ubuntu 24.04 LTS
}

variable "vm_user" {
  description = "Username for SSH access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# =============================================================================
# Network Configuration
# =============================================================================

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "devops-network"
}

variable "subnet_name" {
  description = "Name of the subnet"
  type        = string
  default     = "devops-subnet"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH (for security, use your IP/32)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# =============================================================================
# GitHub Provider Configuration (for bonus task)
# =============================================================================

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
  default     = ""
}

variable "github_repo_name" {
  description = "GitHub repository name to import"
  type        = string
  default     = "DevOps-Core-Course"
}

# =============================================================================
# Tags/Labels
# =============================================================================

variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "lab04"
}

variable "project" {
  description = "Project name for resource tagging"
  type        = string
  default     = "devops-course"
}
