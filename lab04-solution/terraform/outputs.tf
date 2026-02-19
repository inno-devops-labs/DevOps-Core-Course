output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.main.id
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.main.id
}

output "instance_private_ip" {
  description = "Private IP address of the instance"
  value       = aws_instance.main.private_ip
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = aws_eip.main.public_ip
}

output "elastic_ip_id" {
  description = "Elastic IP allocation ID"
  value       = aws_eip.main.id
}

output "ssh_connection_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.main.public_ip}"
}

output "instance_details" {
  description = "Summary of instance details"
  value = {
    instance_id     = aws_instance.main.id
    instance_type   = aws_instance.main.instance_type
    availability_zone = aws_instance.main.availability_zone
    public_ip       = aws_eip.main.public_ip
    private_ip      = aws_instance.main.private_ip
    ami_id          = aws_instance.main.ami
    security_groups = aws_instance.main.security_groups
  }
}
