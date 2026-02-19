output "public_ip" {
  description = "Public IP of the VM"
  value       = aws_instance.this.public_ip
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh ubuntu@${aws_instance.this.public_ip}"
}
