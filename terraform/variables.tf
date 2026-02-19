variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
  sensitive   = true
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
  sensitive   = true
}

variable "service_account_key_file" {
  description = "Path to Yandex Cloud service account key JSON file"
  type        = string
  sensitive   = true
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "devops-vm"
}

variable "vm_description" {
  description = "Description of the virtual machine"
  type        = string
  default     = "DevOps Lab 04 VM - created with Terraform"
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_core_fraction" {
  description = "CPU core fraction (percentage)"
  type        = number
  default     = 20  # Free tier: 20%
}

variable "vm_memory" {
  description = "Amount of RAM in GB"
  type        = number
  default     = 1  # Free tier: 1 GB
}

variable "vm_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10  # Free tier: 10 GB
}

variable "vm_disk_type" {
  description = "Boot disk type"
  type        = string
  default     = "network-hdd"  # Free tier
}

variable "vm_platform_id" {
  description = "VM platform ID"
  type        = string
  default     = "standard-v2"  # Intel Ice Lake
}

variable "image_family" {
  description = "OS image family to use"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "ssh_user" {
  description = "SSH user name"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
  sensitive   = true
}

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

variable "security_group_name" {
  description = "Name of the security group"
  type        = string
  default     = "devops-security-group"
}

variable "allowed_ssh_ip" {
  description = "IP address allowed for SSH access (CIDR notation)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    project   = "devops-course"
    lab       = "lab04"
    managed-by = "terraform"
  }
}
