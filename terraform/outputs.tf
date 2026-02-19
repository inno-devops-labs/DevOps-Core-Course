# VM Outputs
output "vm_id" {
  description = "ID of the created VM instance"
  value       = yandex_compute_instance.vm.id
}

output "vm_name" {
  description = "Name of the created VM instance"
  value       = yandex_compute_instance.vm.name
}

output "public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "internal_ip" {
  description = "Internal IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].ip_address
}

output "ssh_connection_command" {
  description = "Command to SSH into the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}

output "network_id" {
  description = "ID of the created network"
  value       = yandex_vpc_network.network.id
}

output "subnet_id" {
  description = "ID of the created subnet"
  value       = yandex_vpc_subnet.subnet.id
}

output "security_group_id" {
  description = "ID of the created security group"
  value       = yandex_vpc_security_group.sg.id
}

output "vm_fqdn" {
  description = "FQDN of the VM"
  value       = yandex_compute_instance.vm.fqdn
}

output "zone" {
  description = "Availability zone where VM is deployed"
  value       = var.zone
}
