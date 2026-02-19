output "vm_public_ip" {
  value = yandex_compute_instance.main.network_interface[0].nat_ip_address
}

output "vm_name" {
  value = yandex_compute_instance.main.name
}

output "vm_id" {
  value = yandex_compute_instance.main.id
}

output "ssh_connection_command" {
  value = "ssh ${var.ssh_user}@${yandex_compute_instance.main.network_interface[0].nat_ip_address}"
}

output "network_id" {
  value = data.yandex_vpc_network.default.id
}

output "security_group_id" {
  value = yandex_vpc_security_group.main.id
}
