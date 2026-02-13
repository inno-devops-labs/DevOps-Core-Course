terraform {
  required_version = ">= 1.0.0"
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.87.0"
    }
    github = {
      source  = "integrations/github"
      version = ">= 4.0.0"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.service_account_key_file
  folder_id = var.folder_id
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}



data "yandex_vpc_subnet" "lab_subnet" {
  subnet_id = "e9be2kmkd88699e7ojls"
}

resource "yandex_compute_instance" "vm" {
  name        = var.instance_name
  platform_id = "standard-v3"
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
    subnet_id          = data.yandex_vpc_subnet.lab_subnet.id
    nat                = true
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }
}