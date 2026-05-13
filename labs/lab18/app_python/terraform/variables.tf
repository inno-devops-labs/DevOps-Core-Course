variable "zone" {
  description = "Yandex Cloud availability zone"
}

variable "ssh_key_path" {
  description = "Path to the SSH key for VM access"
}

variable "ssh_source_ip" {
  description = "Your IP address to allow SSH access"
}

variable "app_port" {
  description = "Custom app port to open in the firewall"
}
