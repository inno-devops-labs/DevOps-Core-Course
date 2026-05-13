terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  service_account_key_file = "/Users/fountainer/.yandexcloud/my-sa-key.json"
  zone = var.zone
  cloud_id  = "b1g4lhssapi17vlk0t0m"
  folder_id = "b1gcu87lbfoq3i0quvi9"
}

data "yandex_compute_image" "ubuntu_2204" {
  family = "ubuntu-2204-lts"
}

resource "yandex_compute_disk" "boot-disk" {
  name     = "boot-disk-terraform"
  type     = "network-hdd"
  zone     = var.zone
  size     = "20"
  image_id = data.yandex_compute_image.ubuntu_2204.id
}

resource "yandex_compute_instance" "vm" {
  name = "terraform"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    disk_id = yandex_compute_disk.boot-disk.id
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.vm_sg.id]

  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_key_path)}"
  }
}

resource "yandex_vpc_network" "network" {
  name = "network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "subnet1"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

resource "yandex_vpc_security_group" "vm_sg" {
  name       = "vm-security-group"
  network_id = yandex_vpc_network.network.id

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App port"
    port           = var.app_port
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

