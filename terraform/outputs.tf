output "vm_id" {
  description = "VM ID"
  value       = yandex_compute_instance.vm.id
}

output "vm_name" {
  description = "VM Name"
  value       = yandex_compute_instance.vm.name
}

output "vm_private_ip" {
  description = "Private IP address"
  value       = yandex_compute_instance.vm.network_interface[0].ip_address
}

output "vm_public_ip" {
  description = "Public IP address (from NAT)"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "ssh_connection_command" {
  description = "SSH command to connect"
  value       = "ssh ubuntu@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}

output "security_group_id" {
  description = "Security Group ID"
  value       = yandex_vpc_security_group.sg.id
}

output "network_id" {
  description = "VPC Network ID"
  value       = yandex_vpc_network.network.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = yandex_vpc_subnet.subnet.id
}

output "check_web_access" {
  description = "Test web access"
  value       = "curl http://${yandex_compute_instance.vm.network_interface[0].nat_ip_address}:80"
}

# Static IP output (if created)
output "static_ip_address" {
  description = "Static IP address"
  value       = length(yandex_vpc_address.static_ip) > 0 ? yandex_vpc_address.static_ip[0].external_ipv4_address[0].address : null
}