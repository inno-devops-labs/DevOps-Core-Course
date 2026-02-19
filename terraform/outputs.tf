output "public_ip" {
  description = "Public IP address of the VM"
  value       = aws_instance.vm.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.vm.id
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_instance.vm.public_ip}"
}
