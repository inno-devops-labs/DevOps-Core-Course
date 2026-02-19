terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
    service_account_key_file = "/Users/aliiabashirova/.yc/key.json"
    cloud_id  = var.cloud_id
    folder_id = var.folder_id
    zone = "ru-central1-a"
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# ---------------- VPC ----------------

resource "yandex_vpc_network" "network" {
  name = "lab4-network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab4-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.0.0/24"]
}

# ---------------- Security Group ----------------

resource "yandex_vpc_security_group" "sg" {
  name       = "lab4-sg"
  network_id = yandex_vpc_network.network.id

  ingress {
    description    = "SSH from my IP"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.my_ip]
  }

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "App port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------- VM ----------------

resource "yandex_compute_instance" "vm" {
  name        = "lab4-vm"
  platform_id = "standard-v2"

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
  initialize_params {
    image_id = data.yandex_compute_image.ubuntu.id
    size     = 10
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }
}
