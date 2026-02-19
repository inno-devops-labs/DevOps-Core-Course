output "vm_ip" {
  description = "Public IP created by VM"
  value       = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}

output "vm_id" {
  description = "ID VM"
  value       = yandex_compute_instance.vm.id
}
