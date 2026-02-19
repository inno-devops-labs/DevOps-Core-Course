output "public_ip" {
  description = "Public IP of the VM"
  value       = yandex_compute_instance.lab4.network_interface[0].nat_ip_address
}

output "ssh_command" {
  description = "Example SSH command"
  value       = "ssh ubuntu@${yandex_compute_instance.lab4.network_interface[0].nat_ip_address}"
}
