output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = aws_instance.vm.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to VM"
  value       = "ssh ${var.instance_username}@${aws_instance.vm.public_ip}"
}

output "security_group_id" {
  description = "Security group ID for the VM"
  value       = aws_security_group.vm.id
}
