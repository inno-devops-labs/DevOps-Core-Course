variable "vm_name" {
  description = "Name of the VirtualBox VM"
  type        = string
  default     = "ubuntu-devops"
}

variable "vm_image_url" {
  description = "URL to the VM image (Vagrant box)"
  type        = string
  # bento/ubuntu-22.04 — actively maintained box with up-to-date VirtualBox Guest Additions
  default = "https://app.vagrantup.com/bento/boxes/ubuntu-22.04/versions/202407.23.0/providers/virtualbox/amd64/vagrant.box"
}

variable "vm_cpus" {
  description = "Number of CPUs for the VM"
  type        = number
  default     = 2
}

variable "vm_memory" {
  description = "Amount of RAM for the VM in MB"
  type        = number
  default     = 1024
}

variable "host_only_adapter" {
  description = "Name of the VirtualBox host-only network adapter"
  type        = string
  default     = "VirtualBox Host-Only Ethernet Adapter"
}
