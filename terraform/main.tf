terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.135.0"
    }
  }
}

provider "yandex" {
  zone                      = var.zone
  folder_id                 = var.folder_id
  service_account_key_file  = var.sa_key_path
}

# ТВОЯ DEFAULT СЕТЬ (enpbr6bi831c0ecd2stu из консоли)
data "yandex_vpc_network" "default" {
  folder_id = var.folder_id
  name      = "default"
}

resource "yandex_vpc_security_group" "lab_sg" {
  description = "Lab 4: SSH + HTTP + 5000"
  network_id  = data.yandex_vpc_network.default.id  # ← ТВОЯ default сеть!

  ingress {
    protocol       = "TCP"
    from_port      = 22
    to_port        = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    protocol       = "TCP"
    from_port      = 80
    to_port        = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    protocol       = "TCP"
    from_port      = 5000
    to_port        = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_compute_instance" "vm" {
  name        = "lab-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    core_fraction = 20
    memory        = 1
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = "10"
    }
  }

  network_interface {
    subnet_id          = "e9be4stg7uhn6e3u754n"
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
    nat                = true
  }

  metadata = {
    ssh-keys = "ubuntu:${file("~/.ssh/id_ed25519_lab04.pub")}"
  }
}
