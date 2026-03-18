output "public_ip" {
  value = yandex_vpc_address.public_ip.external_ipv4_address[0].address
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/id_ed25519 ${var.vm_user}@${yandex_vpc_address.public_ip.external_ipv4_address[0].address}"
}
