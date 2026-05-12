output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}

output "ssh_connection_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.vm_username}@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}

output "vm_id" {
  description = "ID of the VM instance"
  value       = yandex_compute_instance.lab_vm.id
}

