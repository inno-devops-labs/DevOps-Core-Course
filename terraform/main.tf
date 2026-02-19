# ============================================================
# Terraform configuration for Yandex Cloud VM
# Lab 4 — Infrastructure as Code
# ============================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.133.0"
    }
  }
}

# ------------------------------------------------------------
# Provider — credentials come from environment variables or
# terraform.tfvars (gitignored)
# ------------------------------------------------------------
provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# ------------------------------------------------------------
# Data source — latest Ubuntu 24.04 LTS image
# ------------------------------------------------------------
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts-oslogin"
}

locals {
  effective_network_id = var.existing_network_id != "" ? var.existing_network_id : yandex_vpc_network.lab_network[0].id
  effective_subnet_id  = var.existing_subnet_id != "" ? var.existing_subnet_id : yandex_vpc_subnet.lab_subnet[0].id
}

# ------------------------------------------------------------
# Network
# ------------------------------------------------------------
resource "yandex_vpc_network" "lab_network" {
  count = var.existing_network_id == "" ? 1 : 0
  name  = "lab04-network"
}

resource "yandex_vpc_subnet" "lab_subnet" {
  count          = var.existing_subnet_id == "" ? 1 : 0
  name           = "lab04-subnet"
  zone           = var.yc_zone
  network_id     = local.effective_network_id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

# ------------------------------------------------------------
# Security Group — allow SSH (22), HTTP (80), App (5000)
# ------------------------------------------------------------
resource "yandex_vpc_security_group" "lab_sg" {
  name       = "lab04-sg"
  network_id = local.effective_network_id

  ingress {
    description    = "Allow SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Allow HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Allow app port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# ------------------------------------------------------------
# Compute Instance (free-tier: 2 cores @ 20%, 1 GB RAM)
# ------------------------------------------------------------
resource "yandex_compute_instance" "lab_vm" {
  name        = "lab04-vm"
  platform_id = "standard-v2"
  zone        = var.yc_zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = local.effective_subnet_id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = "devops-lab04"
    tool    = "terraform"
  }
}
