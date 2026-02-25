output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.devops.network_interface[0].nat_ip_address
}

output "vm_id" {
  description = "ID of the compute instance"
  value       = yandex_compute_instance.devops.id
}

output "ssh_connection" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.ssh_user}@${yandex_compute_instance.devops.network_interface[0].nat_ip_address}"
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.devops.id
}
