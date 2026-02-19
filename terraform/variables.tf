variable "cloud_id" { type = string }
variable "folder_id" { type = string }
variable "zone" {
  type    = string
  default = "ru-central1-a"
}

variable "service_account_key_file" {
  type        = string
  description = "Path to SA key.json (do not commit)"
}

variable "ssh_user" {
  type    = string
  default = "ubuntu"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to your public key, e.g. ~/.ssh/id_ed25519.pub"
}

variable "my_ssh_cidr" {
  type        = string
  description = "Your public IP in CIDR for SSH, e.g. 1.2.3.4/32"
}

variable "subnet_cidr" {
  type    = string
  default = "10.10.0.0/24"
}