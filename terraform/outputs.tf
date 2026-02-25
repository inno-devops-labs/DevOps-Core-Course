output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address
}

output "vm_name" {
  description = "Name of the VM"
  value       = yandex_compute_instance.lab04_vm.name
}

output "vm_id" {
  description = "ID of the VM"
  value       = yandex_compute_instance.lab04_vm.id
}

output "ssh_connection_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh -i ~/.ssh/id_ed25519 ubuntu@${yandex_compute_instance.lab04_vm.network_interface[0].nat_ip_address}"
}

output "network_id" {
  description = "ID of the VPC network"
  value       = yandex_vpc_network.lab04_network.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.lab04_subnet.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = yandex_vpc_security_group.lab04_sg.id
}
