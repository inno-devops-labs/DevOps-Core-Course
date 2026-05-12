variable "cloud_id" {
  description = "Yandex Cloud ID where resources will be created"
  type        = string
}

variable "folder_id" {
  description = "Yandex Cloud Folder ID where resources will be created"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "service_account_key_file" {
  description = "Path to the service account key JSON file"
  type        = string
  default     = "inno-key.json"
}

variable "public_key_path" {
  description = "Path to the public SSH key for VM access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "instance_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "lab4-vm"
}

variable "vm_username" {
  description = "Username for SSH access to the VM"
  type        = string
  default     = "ubuntu"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC network"
  type        = string
  default     = "192.168.10.0/24"
}
