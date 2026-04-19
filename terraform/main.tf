terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.80"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  token     = var.yc_token
}

data "yandex_vpc_network" "default" {
  name = "default"
}

resource "yandex_vpc_subnet" "subnet-1" {
  name           = "subnet-terraform"
  zone           = var.zone
  network_id     = data.yandex_vpc_network.default.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

resource "yandex_compute_disk" "boot-disk-1" {
  name     = "boot-disk-1"
  type     = "network-hdd"
  zone     = var.zone
  size     = 20
  image_id = "fd84kd8dcu6tmnhbeebv"
}

resource "yandex_compute_instance" "vm-1" {
  name = var.vm_name
  zone = var.zone

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    disk_id = yandex_compute_disk.boot-disk-1.id
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-1.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${trimspace(var.ssh_public_key)}"
  }
}