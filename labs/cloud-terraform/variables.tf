variable "zone" {
  description = "Yandex Cloud availability zone"
  type        = string
  default     = "ru-central1-b"
}

variable "project_name" {
  description = "Prefix for resource names"
  type        = string
  default     = "myapp"
}

variable "labels" {
  description = "Common labels applied to all resources"
  type        = map(string)
  default = {
    environment = "dev"
    managed_by  = "terraform"
  }
}

variable "image_family" {
  description = "Family of the public image to use"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "subnet_cidr" {
  description = "CIDR block for the subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_cores" {
  description = "Number of CPU cores for the VM"
  type        = number
  default     = 2 
}

variable "instance_memory" {
  description = "Amount of RAM in GB"
  type        = number
  default     = 2 
}

variable "boot_disk_size" {
  description = "Boot disk size in GB"
  type        = number
  default     = 20
}

variable "ssh_public_key" {
  description = "Contents of your SSH public key (e.g., cat ~/.ssh/id_rsa.pub)"
  type        = string
  sensitive   = true
}

variable "allowed_ssh_ips" {
  description = "List of CIDR blocks allowed to SSH (set to your public IP for security)"
  type        = list(string)
  default     = ["188.130.155.186/32"]
}

variable "folder_id" {
  description = "Yandex Cloud folder ID where resources will be created"
  type        = string
}

variable "oauth_token" {
  description = "OAuth token"
  type        = string
}
