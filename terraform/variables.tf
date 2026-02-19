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

variable "my_ip" {
  type        = string
  description = "185.252.144.192/32"
}

variable "ssh_public_key_path" {
  type    = string
  default = "/Users/aliiabashirova/.ssh/id_rsa.pub"
}
