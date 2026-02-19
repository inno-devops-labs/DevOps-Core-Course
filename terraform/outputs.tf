locals {
  public_ip = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

# Public IP of the virtual machine for remote access
output "public_ip" {
  value = local.public_ip
}

# SSH command for quick connection to VM
output "ssh_cmd" {
  value = "ssh ${var.ssh_username}@${local.public_ip}"
}
