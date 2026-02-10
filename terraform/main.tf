# =============================================================================
# Provider Configuration
# =============================================================================

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# Conditionally configure GitHub provider (for bonus task)
provider "github" {
  token = var.github_token != "" ? var.github_token : null
  owner = var.github_owner != "" ? var.github_owner : null
}

# =============================================================================
# Data Sources
# =============================================================================

# Get the SSH public key content
locals {
  ssh_public_key = file(pathexpand(var.ssh_public_key_path))
}

# =============================================================================
# Network Resources
# =============================================================================

# Create VPC Network
resource "yandex_vpc_network" "main" {
  name        = var.network_name
  description = "VPC network for DevOps course Lab 4"

  labels = {
    environment = var.environment
    project     = var.project
  }
}

# Create Subnet
resource "yandex_vpc_subnet" "main" {
  name           = var.subnet_name
  description    = "Subnet for DevOps VM"
  zone           = var.yc_zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = [var.subnet_cidr]

  labels = {
    environment = var.environment
    project     = var.project
  }
}

# =============================================================================
# Security Group (Firewall)
# =============================================================================

resource "yandex_vpc_security_group" "main" {
  name        = "devops-security-group"
  description = "Security group for DevOps VM"
  network_id  = yandex_vpc_network.main.id

  labels = {
    environment = var.environment
    project     = var.project
  }

  # Allow SSH (port 22)
  ingress {
    description    = "Allow SSH access"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = var.allowed_ssh_cidr
  }

  # Allow HTTP (port 80)
  ingress {
    description    = "Allow HTTP access"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow custom app port (port 5000)
  ingress {
    description    = "Allow Flask app access"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS (port 443)
  ingress {
    description    = "Allow HTTPS access"
    protocol       = "TCP"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow ICMP (ping)
  ingress {
    description    = "Allow ICMP (ping)"
    protocol       = "ICMP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# =============================================================================
# Compute Instance (VM)
# =============================================================================

resource "yandex_compute_instance" "main" {
  name        = var.vm_name
  platform_id = var.vm_platform_id
  zone        = var.yc_zone
  hostname    = var.vm_name

  labels = {
    environment = var.environment
    project     = var.project
  }

  resources {
    cores         = var.vm_cores
    memory        = var.vm_memory
    core_fraction = var.vm_core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = var.vm_image_id
      size     = var.vm_disk_size
      type     = var.vm_disk_type
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.main.id
    nat                = true # Enable public IP
    security_group_ids = [yandex_vpc_security_group.main.id]
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${local.ssh_public_key}"
  }

  scheduling_policy {
    preemptible = true # Use preemptible VM for cost savings
  }
}

# =============================================================================
# GitHub Repository Import (Bonus Task)
# =============================================================================

# This resource is for importing an existing GitHub repository
# Run: terraform import github_repository.course_repo DevOps-Core-Course
resource "github_repository" "course_repo" {
  count = var.github_token != "" ? 1 : 0

  name        = var.github_repo_name
  description = "DevOps course lab assignments and infrastructure"
  visibility  = "public"

  has_issues   = true
  has_wiki     = false
  has_projects = false

  allow_merge_commit = true
  allow_squash_merge = true
  allow_rebase_merge = true

  delete_branch_on_merge = false
  auto_init              = false
}
