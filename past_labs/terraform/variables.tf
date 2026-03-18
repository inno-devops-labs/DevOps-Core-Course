variable "cloud_id" {
  type = string
}

variable "folder_id" {
  type = string
}

variable "zone" {
  type    = string
  default = "ru-central1-a"
}

variable "vm_name" {
  type    = string
  default = "lab-vm"
}

variable "vm_user" {
  type    = string
  default = "ubuntu"
}

variable "ssh_public_key_path" {
  type = string
}

variable "sa_key_path" {
  type = string
}

variable "ssh_allow_cidr" {
  description = "188.130.155.177/32"
  type        = string
}

variable "subnet_cidr" {
  type    = string
  default = "10.10.0.0/24"
}

variable "cores" {
  type    = number
  default = 2
}

variable "memory_gb" {
  type    = number
  default = 2
}

variable "core_fraction" {
  type    = number
  default = 20
}

variable "labels" {
  type = map(string)
  default = {
    project = "lab04"
  }
}
