# VM Information
output "vm_id" {
  description = "OCID of the created VM"
  value       = oci_core_instance.lab04_vm.id
}

output "vm_name" {
  description = "Name of the created VM"
  value       = oci_core_instance.lab04_vm.display_name
}

output "vm_state" {
  description = "State of the VM"
  value       = oci_core_instance.lab04_vm.state
}

# Network Information
output "public_ip" {
  description = "Public IP address of the VM"
  value       = oci_core_instance.lab04_vm.public_ip
}

output "private_ip" {
  description = "Private IP address of the VM"
  value       = oci_core_instance.lab04_vm.private_ip
}

# SSH Connection
output "ssh_connection_string" {
  description = "SSH connection command"
  value       = "ssh -i ~/.ssh/oracle_cloud_key ${var.ssh_user}@${oci_core_instance.lab04_vm.public_ip}"
}

# Resource Information
output "vcn_id" {
  description = "OCID of the created VCN"
  value       = oci_core_vcn.lab04_vcn.id
}

output "subnet_id" {
  description = "OCID of the created subnet"
  value       = oci_core_subnet.lab04_subnet.id
}

output "availability_domain" {
  description = "Availability domain where VM is created"
  value       = oci_core_instance.lab04_vm.availability_domain
}

output "shape" {
  description = "Shape of the VM (Free Tier)"
  value       = oci_core_instance.lab04_vm.shape
}
