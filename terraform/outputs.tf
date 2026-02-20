output "instance_public_ip" {
  description = "Public IP address of the VM"
  value       = google_compute_instance.vm.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ubuntu@${google_compute_instance.vm.network_interface[0].access_config[0].nat_ip}"
}
