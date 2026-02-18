output "vm_public_ip" {
  description = "Public IP of the VPS"
  value       = var.ssh_host
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh ${var.ssh_user}@${var.ssh_host}"
}
