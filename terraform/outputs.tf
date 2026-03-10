# VM Information
output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.lab04_vm.id
}

output "vm_name" {
  description = "Name of the created VM"
  value       = yandex_compute_instance.lab04_vm.name
}

output "vm_fqdn" {
  description = "FQDN of the created VM"
  value       = yandex_compute_instance.lab04_vm.fqdn
}

# Network Information
output "internal_ip" {
  description = "Internal IP address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].ip_address
}

output "external_ip" {
  description = "External (public) IP address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address
}

# SSH Connection
output "ssh_connection_string" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/yandex_cloud_key ${var.ssh_user}@${yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address}"
}

# Resource Information
output "network_id" {
  description = "ID of the created network"
  value       = yandex_vpc_network.lab04_network.id
}

output "subnet_id" {
  description = "ID of the created subnet"
  value       = yandex_vpc_subnet.lab04_subnet.id
}

# Security group output removed - using default security group
