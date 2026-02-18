output "vm_id" {
  description = "ID of the created VM instance"
  value       = yandex_compute_instance.lab_vm.id
}

output "vm_name" {
  description = "Name of the created VM instance"
  value       = yandex_compute_instance.lab_vm.name
}

output "vm_external_ip" {
  description = "External (public) IP address of the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}

output "vm_internal_ip" {
  description = "Internal IP address of the VM"
  value       = yandex_compute_instance.lab_vm.network_interface[0].ip_address
}

output "vm_fqdn" {
  description = "Fully qualified domain name of the VM"
  value       = yandex_compute_instance.lab_vm.fqdn
}

output "ssh_connection_command" {
  description = "Command to SSH into the VM"
  value       = "ssh ubuntu@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}

output "network_id" {
  description = "ID of the VPC network"
  value       = yandex_vpc_network.lab_network.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.lab_subnet.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = yandex_vpc_security_group.lab_sg.id
}

output "zone" {
  description = "Availability zone where resources are created"
  value       = var.zone
}

output "vm_status" {
  description = "Status of the VM instance"
  value       = yandex_compute_instance.lab_vm.status
}
