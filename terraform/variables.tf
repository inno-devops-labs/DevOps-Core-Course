variable "ssh_host" {
  description = "IP address of the remote server"
  type        = string
}

variable "ssh_user" {
  description = "SSH username"
  type        = string
  default     = "not_your_business"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key"
  type        = string
  default     = "~/go_touch_grass"
}
