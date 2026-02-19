# =============================================================================
# VM Outputs
# =============================================================================

output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.main.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.main.network_interface[0].ip_address
}

output "vm_id" {
  description = "ID of the compute instance"
  value       = yandex_compute_instance.main.id
}

output "vm_name" {
  description = "Name of the compute instance"
  value       = yandex_compute_instance.main.name
}

output "vm_fqdn" {
  description = "FQDN of the compute instance"
  value       = yandex_compute_instance.main.fqdn
}

# =============================================================================
# Network Outputs
# =============================================================================

output "network_id" {
  description = "ID of the VPC network"
  value       = yandex_vpc_network.main.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = yandex_vpc_subnet.main.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = var.enable_security_group ? yandex_vpc_security_group.main[0].id : "Security group disabled"
}

# =============================================================================
# Connection Outputs
# =============================================================================

output "ssh_connection_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.vm_user}@${yandex_compute_instance.main.network_interface[0].nat_ip_address}"
}

output "vm_zone" {
  description = "Availability zone of the VM"
  value       = yandex_compute_instance.main.zone
}

# =============================================================================
# GitHub Repository Outputs (Bonus Task)
# =============================================================================

output "github_repo_url" {
  description = "GitHub repository URL"
  value       = var.enable_github_bonus ? github_repository.course_repo[0].html_url : "GitHub bonus disabled"
  sensitive   = true
}

output "github_repo_clone_url" {
  description = "GitHub repository clone URL"
  value       = var.enable_github_bonus ? github_repository.course_repo[0].git_clone_url : "GitHub bonus disabled"
  sensitive   = true
}
