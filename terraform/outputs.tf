output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].ip_address
}

output "vm_id" {
  description = "ID of the VM instance"
  value       = yandex_compute_instance.vm.id
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}

output "network_id" {
  description = "VPC Network ID"
  value       = yandex_vpc_network.network.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = yandex_vpc_subnet.subnet.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = yandex_vpc_security_group.sg.id
}
