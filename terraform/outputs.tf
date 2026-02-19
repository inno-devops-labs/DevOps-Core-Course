output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}

output "vm_name" {
  description = "Name of the created VM"
  value       = yandex_compute_instance.lab_vm.name
}

output "ssh_connection" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}

output "subnet_id" {
  description = "ID of the created subnet"
  value       = yandex_vpc_subnet.lab_subnet.id
}
