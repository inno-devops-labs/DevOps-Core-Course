output "public_ip" {
  description = "Public IP assigned to VM"
  value       = aws_eip.web_eip.public_ip
}

output "instance_id" {
  value = aws_instance.vm.id
}
