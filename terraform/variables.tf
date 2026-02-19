variable "prefix" {
  type    = string
  default = "lab04"
}

variable "zone" {
  type    = string
  default = "ru-central1-a"
}

variable "subnet_cidr" {
  type    = string
  default = "10.10.0.0/24"
}

variable "platform_id" {
  type    = string
  default = "standard-v2"
}

variable "cores" {
  type    = number
  default = 2
}

variable "memory_gb" {
  type    = number
  default = 1
}

variable "core_fraction" {
  type    = number
  default = 20
}

variable "disk_gb" {
  type    = number
  default = 10
}

variable "disk_type" {
  type    = string
  default = "network-hdd"
}

variable "image_family" {
  type    = string
  default = "ubuntu-2204-lts"
}

variable "vm_name" {
  type    = string
  default = "lab04-vm"
}

variable "ssh_username" {
  type    = string
  default = "ubuntu"
}

variable "ssh_public_key_path" {
  type = string
}

variable "ssh_allowed_cidr" {
  type = string
}
