output "instance_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "ssh_command" {
  description = "Example SSH command to connect to the VM"
  value       = "ssh ubuntu@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}
