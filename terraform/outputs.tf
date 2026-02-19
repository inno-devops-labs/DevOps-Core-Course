# ============================================================
# Outputs — displayed after terraform apply
# ============================================================

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
  value       = "ssh ${var.vm_user}@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}

output "subnet_id" {
  description = "Subnet ID"
  value       = local.effective_subnet_id
}

output "security_group_id" {
  description = "Security group ID"
  value       = yandex_vpc_security_group.lab_sg.id
}
