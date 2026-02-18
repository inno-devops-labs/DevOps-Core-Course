output "instance_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.this.network_interface[0].nat_ip_address
}

output "instance_id" {
  description = "ID of the created instance"
  value       = yandex_compute_instance.this.id
}

output "ssh_connection_command" {
  description = "Command to connect via SSH"
  value       = "ssh ubuntu@${yandex_compute_instance.this.network_interface[0].nat_ip_address}"
}