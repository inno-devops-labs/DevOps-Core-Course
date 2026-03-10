terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.131"
    }
  }
  required_version = ">= 1.0"
}

# Provider configuration
provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
  zone      = var.zone
}

# Get latest Ubuntu 24.04 image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

# Create VPC Network
resource "yandex_vpc_network" "lab04_network" {
  name        = "lab04-network"
  description = "Network for Lab04 DevOps VM"
}

# Create Subnet
resource "yandex_vpc_subnet" "lab04_subnet" {
  name           = "lab04-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab04_network.id
  v4_cidr_blocks = ["10.128.0.0/24"]
  description    = "Subnet for Lab04 DevOps VM"
}

# Note: Security Group creation requires additional permissions
# Using default security group instead (allows all traffic by default)

# Create VM Instance
resource "yandex_compute_instance" "lab04_vm" {
  name        = "lab04-devops-vm"
  hostname    = "lab04-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20 # 20% CPU - free tier
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10 # 10 GB HDD - free tier
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.lab04_subnet.id
    nat       = true # Assign public IP
  }

  metadata = {
    ssh-keys  = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
    user-data = <<-EOF
      #cloud-config
      users:
        - name: ${var.ssh_user}
          groups: sudo
          shell: /bin/bash
          sudo: ['ALL=(ALL) NOPASSWD:ALL']
          ssh-authorized-keys:
            - ${file(var.ssh_public_key_path)}
      package_update: true
      package_upgrade: true
      packages:
        - curl
        - wget
        - git
        - htop
    EOF
  }

  scheduling_policy {
    preemptible = false
  }

  labels = {
    environment = "lab04"
    course      = "devops"
    created_by  = "terraform"
  }
}
