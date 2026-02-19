variable "vm_name" {
  description = "Name of the local VM"
  type        = string
}

variable "vm_ip" {
  description = "IP address of the local VM"
  type        = string
}

variable "ssh_user" {
  description = "SSH username"
  type        = string
  default     = "ubuntu"
}
