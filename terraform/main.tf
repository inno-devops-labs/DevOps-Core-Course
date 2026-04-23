##############################################
# Terraform — Yandex Cloud VM
##############################################

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.130.0"
    }
  }
}

# -----------------------------------------------
# Provider
# -----------------------------------------------
provider "yandex" {
  token     = var.yc_token
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# -----------------------------------------------
# Data source — latest Ubuntu 24.04 image
# -----------------------------------------------
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

# -----------------------------------------------
# Network
# -----------------------------------------------
resource "yandex_vpc_network" "main" {
  name = "devops-network"
}

resource "yandex_vpc_subnet" "main" {
  name           = "devops-subnet"
  zone           = var.yc_zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

# -----------------------------------------------
# Compute Instance (free tier)
# -----------------------------------------------
resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = "standard-v2"
  zone        = var.yc_zone

  labels = {
    project = "devops-course"
    lab     = "lab04"
  }

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
    subnet_id = yandex_vpc_subnet.main.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  scheduling_policy {
    preemptible = true
  }
}

