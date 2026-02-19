output "vm_name" {
  description = "Name of the created VM"
  value       = var.vm_name
}

output "ssh_command" {
  description = "SSH connection command (NAT port forwarding)"
  value       = "ssh -p 2222 vagrant@127.0.0.1  # password: vagrant"
}

output "host_only_ip" {
  description = "Get host-only IP after VM boots"
  value       = "& 'C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe' guestproperty get ${var.vm_name} /VirtualBox/GuestInfo/Net/1/V4/IP"
}
