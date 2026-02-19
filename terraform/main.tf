terraform {
  required_version = ">= 1.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "local" {}

resource "local_file" "vm_info" {
  filename = "${path.module}/vm_info.txt"

  content = <<EOT
Virtual Machine Information
---------------------------
VM Name: ${var.vm_name}
VM IP: ${var.vm_ip}
SSH User: ${var.ssh_user}
SSH Command: ssh ${var.ssh_user}@${var.vm_ip}
EOT
}
