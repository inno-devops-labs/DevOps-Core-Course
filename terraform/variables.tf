variable "yandex_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yandex_folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "yandex_zone" {
  description = "Yandex Cloud zone (e.g., ru-central1-a)"
  type        = string
  default     = "ru-central1-a"
}

variable "vm_name" {
  description = "Name of the virtual machine"
  type        = string
  default     = "lab04-vm"
}

variable "vm_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "vm_core_fraction" {
  description = "CPU core fraction (20% for free tier)"
  type        = number
  default     = 20
}

variable "vm_memory" {
  description = "Memory in GB"
  type        = number
  default     = 1
}

variable "vm_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "vm_image_family" {
  description = "OS image family (e.g., ubuntu-2204-lts)"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "lab04-network"
}

variable "subnet_name" {
  description = "Name of the subnet"
  type        = string
  default     = "lab04-subnet"
}

variable "subnet_cidr" {
  description = "CIDR block for subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "my_ip" {
  description = "IP address for SSH access"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_user" {
  description = "SSH username (usually 'ubuntu' for Ubuntu images)"
  type        = string
  default     = "ubuntu"
}
