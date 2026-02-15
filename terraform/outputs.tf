output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}

output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.lab_vm.id
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/id_ed25519 ubuntu@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}
