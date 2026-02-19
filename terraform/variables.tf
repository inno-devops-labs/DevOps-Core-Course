variable "zone" {
  type        = string
  description = "YC availability zone"
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  type        = string
  description = "Subnet CIDR"
  default     = "10.10.0.0/24"
}

variable "my_ip_cidr" {
  type        = string
  description = "Your public IP in CIDR /32 for SSH access"
}

variable "ssh_user" {
  type        = string
  description = "Linux user for SSH"
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to public SSH key"
  default     = "~/.ssh/yc_lab.pub"
}

variable "platform_id" {
  type        = string
  description = "YC platform id"
  default     = "standard-v3"
}

variable "cores" {
  type    = number
  default = 2
}

variable "core_fraction" {
  type    = number
  default = 20
}

variable "memory_gb" {
  type    = number
  default = 1
}

variable "boot_disk_gb" {
  type    = number
  default = 10
}

variable "image_id" {
  type        = string
  description = "Boot disk image id"
}
