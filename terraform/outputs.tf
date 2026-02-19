output "vm_public_ip" {
  value = yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address
}

output "ssh_command" {
  value = "ssh ubuntu@${yandex_compute_instance.lab_vm.network_interface[0].nat_ip_address}"
}
