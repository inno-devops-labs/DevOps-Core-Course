terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  zone = "ru-central1-a"
  folder_id = var.folder_id
  service_account_key_file = var.key_file
}

# Network
resource "yandex_vpc_network" "lab_network" {
  name = "lab-network"
}

# Subnet
resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "lab-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# Security group
resource "yandex_vpc_security_group" "lab_sg" {
  name       = "lab-security-group"
  network_id = yandex_vpc_network.lab_network.id

  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]   # Replace with your IP for security
  }
  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# VM instance (free tier)
resource "yandex_compute_instance" "lab_vm" {
  name        = "lab-vm"
  platform_id = "standard-v2"
  zone        = "ru-central1-a"

  resources {
    cores  = 2
    memory = 1
    core_fraction = 20   # 20% CPU guaranteed
  }

  boot_disk {
    initialize_params {
      image_id = "fd8t9g30r3pc23et5krl"   # Ubuntu 22.04 LTS
      size     = 10
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab_subnet.id
    nat                = true              # Assign public IP
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.public_key_path)}"
  }
}
