output "public_ip" {
  description = "Public IP address of the VM"
  value       = aws_eip.lab04.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.lab04.id
}

output "ami_id" {
  description = "AMI used for the instance"
  value       = data.aws_ami.ubuntu.id
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh -i ~/.ssh/devops-lab04 ubuntu@${aws_eip.lab04.public_ip}"
}
