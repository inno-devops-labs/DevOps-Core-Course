output "public_ip" {
  description = "Public Elastic IP address of the VM."
  value       = aws_eip.vm.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the VM."
  value       = format("ssh -i %s ubuntu@%s", replace(var.public_key_path, ".pub", ""), aws_eip.vm.public_ip)
}

output "security_group_id" {
  description = "Security group ID."
  value       = aws_security_group.vm.id
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.vm.id
}

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

