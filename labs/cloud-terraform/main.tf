terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone = var.zone
  token = var.oauth_token
  folder_id = var.folder_id
}

# Data source for the latest Ubuntu 22.04 LTS image
data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

# VPC Network
resource "yandex_vpc_network" "this" {
  name        = "${var.project_name}-net"
  description = "VPC for ${var.project_name}"
  labels      = var.labels
}

# VPC Subnet
resource "yandex_vpc_subnet" "this" {
  name           = "${var.project_name}-subnet"
  description    = "Subnet in ${var.zone}"
  v4_cidr_blocks = [var.subnet_cidr]
  zone           = var.zone
  network_id     = yandex_vpc_network.this.id
  labels         = var.labels
}

# Security Group
resource "yandex_vpc_security_group" "this" {
  name        = "${var.project_name}-sg"
  description = "Security group for ${var.project_name}"
  network_id  = yandex_vpc_network.this.id
  labels      = var.labels

  # Ingress: SSH from your IP (or anywhere if variable not set)
  dynamic "ingress" {
    for_each = var.allowed_ssh_ips
    content {
      protocol       = "TCP"
      port           = 22
      v4_cidr_blocks = [ingress.value]
      description    = "SSH access"
    }
  }

  # Ingress: HTTP from anywhere
  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "HTTP access"
  }

  # Ingress: Custom port 5000 from anywhere
  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Custom app port"
  }

  # Egress: allow all outgoing traffic
  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow all outgoing"
  }
}

# Compute Instance
resource "yandex_compute_instance" "this" {
  name        = "${var.project_name}-vm"
  description = "Smallest free‑tier VM"
  zone        = var.zone
  labels      = var.labels

  resources {
    cores  = var.instance_cores
    memory = var.instance_memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.boot_disk_size
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.this.id
    nat                = true                     # assigns a public IP
    security_group_ids = [yandex_vpc_security_group.this.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }
}