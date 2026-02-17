variable "cloud_id" { type = string }
variable "folder_id" { type = string }

variable "zone" {
  type    = string
  default = "ru-central1-a"
}

variable "vm_name" {
  type    = string
  default = "lab04-vm"
}

variable "ssh_user" {
  type    = string
  default = "ubuntu"
}

variable "ssh_public_key_path" {
  type = string
}

variable "my_ip_cidr" {
  type        = string
  description = "Your public IP in CIDR, e.g. 1.2.3.4/32"
}

variable "sa_key_file" {
  type        = string
  description = "Path to service account key json"
}
