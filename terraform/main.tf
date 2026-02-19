terraform {
  required_version = ">= 1.9.0"
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_vpc_network" "net" {
  name = "lab04-net"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab04-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "sg" {
  name       = "lab04-sg"
  network_id = yandex_vpc_network.net.id

  # SSH только с твоего IP
  ingress {
    protocol       = "TCP"
    description    = "SSH from my IP"
    v4_cidr_blocks = [var.my_ssh_cidr]
    port           = 22
  }

  # HTTP
  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  # App port
  ingress {
    protocol       = "TCP"
    description    = "App 5000"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  # Исходящий трафик наружу (чтобы apt работал)
  egress {
    protocol       = "ANY"
    description    = "Allow all egress"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "vm" {
  name        = "lab04-vm"
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
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    # формат "user:<contents_of_pubkey>"
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }
}