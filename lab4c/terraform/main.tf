terraform {
  required_version = ">= 1.9"
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  zone                    = var.yandex_zone
  folder_id               = var.yandex_folder_id
  service_account_key_file = var.yandex_service_account_key_file
}

# Ubuntu 22.04
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

resource "yandex_vpc_network" "lab4" {
  name = "lab4c-network"
}

resource "yandex_vpc_subnet" "lab4" {
  name           = "lab4c-subnet"
  network_id     = yandex_vpc_network.lab4.id
  zone           = var.yandex_zone
  v4_cidr_blocks = ["10.0.1.0/24"]
}

resource "yandex_vpc_security_group" "lab4" {
  name        = "lab4c-vm-sg"
  network_id  = yandex_vpc_network.lab4.id
  description = "Allow SSH, HTTP, and port 5000 for Lab 4"

  ingress {
    description = "SSH"
    port        = 22
    protocol    = "TCP"
    v4_cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description    = "HTTP"
    port           = 80
    protocol       = "TCP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "App 5000"
    port           = 5000
    protocol       = "TCP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Any"
    from_port      = 0
    to_port        = 65535
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "lab4" {
  name        = "lab4c-vm"
  platform_id = "standard-v3"
  zone        = var.yandex_zone
  folder_id   = var.yandex_folder_id

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size    = 10
      type    = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab4.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab4.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  labels = {
    lab = "lab04"
  }
}
