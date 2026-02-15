terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.87.0"
    }
  }
  required_version = ">= 1.0"
}

provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

# Network
resource "yandex_vpc_network" "lab_network" {
  name = "lab-network"
}

# Subnet
resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "lab-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

# Security group
resource "yandex_vpc_security_group" "lab_sg" {
  name       = "lab-security-group"
  network_id = yandex_vpc_network.lab_network.id

  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow SSH"
  }

  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow HTTP"
  }

  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow app port 5000"
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "Allow all outbound"
  }
}

# Compute instance (free tier: 2 vCPU 20%, 1GB RAM, 10GB HDD)
resource "yandex_compute_instance" "lab_vm" {
  name        = "lab-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab_subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = "devops-lab04"
    task    = "terraform"
  }
}
