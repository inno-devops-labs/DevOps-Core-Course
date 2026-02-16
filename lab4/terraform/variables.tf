variable "cloud_id" {
  description = "Yandex Cloud ID."
  type        = string
  default     = null
  nullable    = true
}

variable "folder_id" {
  description = "Yandex Cloud folder ID where resources will be created."
  type        = string
}

variable "zone" {
  description = "Yandex Cloud availability zone."
  type        = string
  default     = "ru-central1-a"
}

variable "vm_name" {
  description = "Name for the VM instance."
  type        = string
  default     = "lab04-terraform-vm"
}

variable "network_name" {
  description = "Name for the VPC network."
  type        = string
  default     = "lab04-network"
}

variable "subnet_name" {
  description = "Name for the subnet."
  type        = string
  default     = "lab04-subnet"
}

variable "security_group_name" {
  description = "Name for the security group."
  type        = string
  default     = "lab04-security-group"
}

variable "subnet_cidr_block" {
  description = "IPv4 CIDR block for the subnet."
  type        = string
  default     = "10.10.0.0/24"
}

variable "existing_instance_id_for_network" {
  description = "Optional existing VM instance ID. When set, Terraform reuses that VM subnet/network instead of creating a new VPC and subnet."
  type        = string
  default     = null
  nullable    = true
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to connect over SSH (usually your public IP with /32)."
  type        = string

  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0))
    error_message = "ssh_allowed_cidr must be a valid CIDR block, e.g. 203.0.113.10/32."
  }
}

variable "ssh_user" {
  description = "Linux username used for SSH metadata."
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Absolute path to your public SSH key (for example /Users/me/.ssh/id_ed25519.pub)."
  type        = string
}

variable "image_family" {
  description = "Yandex image family for the VM boot disk."
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "cores" {
  description = "Number of VM CPU cores (free tier recommendation: 2)."
  type        = number
  default     = 2
}

variable "core_fraction" {
  description = "Guaranteed CPU fraction percentage (free tier recommendation: 20)."
  type        = number
  default     = 20
}

variable "memory" {
  description = "VM memory in GB (free tier recommendation: 1)."
  type        = number
  default     = 1
}

variable "boot_disk_size" {
  description = "Boot disk size in GB."
  type        = number
  default     = 10
}

variable "boot_disk_type" {
  description = "Boot disk type."
  type        = string
  default     = "network-hdd"
}

variable "preemptible" {
  description = "Whether VM should be preemptible."
  type        = bool
  default     = false
}

variable "resource_labels" {
  description = "Labels to attach to supported resources."
  type        = map(string)
  default = {
    managed_by = "terraform"
    lab        = "lab04"
  }
}

variable "yc_token" {
  description = "Optional Yandex IAM token. Prefer environment variables for secrets."
  type        = string
  default     = null
  sensitive   = true
  nullable    = true
}

variable "service_account_key_file" {
  description = "Optional absolute path to Yandex service account authorized key JSON."
  type        = string
  default     = null
  nullable    = true
}
