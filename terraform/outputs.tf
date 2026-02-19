output "public_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.vm.network_interface.0.nat_ip_address
}

output "ssh_command" {
  description = "SSH command to connect to VM"
  value       = "ssh ubuntu@${yandex_compute_instance.vm.network_interface.0.nat_ip_address}"
}

output "instance_id" {
  description = "VM Instance ID"
  value       = yandex_compute_instance.vm.id
}
