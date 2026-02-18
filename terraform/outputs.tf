output "vm_public_ip" {
  value = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "vm_id" {
  value = yandex_compute_instance.vm.id
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/id_rsa ubuntu@${yandex_compute_instance.vm.network_interface[0].nat_ip_address}"
}
