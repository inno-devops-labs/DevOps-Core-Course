output "vm_name" {
  description = "VM name"
  value       = var.vm_name
}

output "vm_ip" {
  description = "VM IP address"
  value       = var.vm_ip
}

output "ssh_command" {
  description = "Command to connect to VM via SSH"
  value       = "ssh ${var.ssh_user}@${var.vm_ip}"
}
