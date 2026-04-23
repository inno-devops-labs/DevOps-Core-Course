##############################################
# Outputs
##############################################

output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].ip_address
}

output "vm_id" {
  description = "ID of the compute instance"
  value       = yandex_compute_instance.vm.id
}

output "vm_name" {
  description = "Name of the compute instance"
  value       = yandex_compute_instance.vm.name
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ubuntu@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}

