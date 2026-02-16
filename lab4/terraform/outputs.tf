output "vm_id" {
  description = "ID of the created VM."
  value       = yandex_compute_instance.lab04.id
}

output "vm_public_ip" {
  description = "Public IPv4 address of the VM."
  value       = yandex_vpc_address.lab04.external_ipv4_address[0].address
}

output "vm_internal_ip" {
  description = "Internal IPv4 address of the VM."
  value       = yandex_compute_instance.lab04.network_interface[0].ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the VM."
  value       = "ssh ${var.ssh_user}@${yandex_vpc_address.lab04.external_ipv4_address[0].address}"
}
