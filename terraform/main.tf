terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 1.9"
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# Network — use existing default network (free tier has quota of 1 network)

data "yandex_vpc_network" "default" {
  name = "default"
}

resource "yandex_vpc_subnet" "main" {
  name           = "${var.project_name}-subnet"
  zone           = var.yc_zone
  network_id     = data.yandex_vpc_network.default.id
  v4_cidr_blocks = ["10.0.0.0/24"]
}

# Security Group

resource "yandex_vpc_security_group" "main" {
  name       = "${var.project_name}-sg"
  network_id = data.yandex_vpc_network.default.id

  ingress {
    protocol       = "TCP"
    description    = "SSH access"
    port           = 22
    v4_cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App port 5000"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Compute Instance

resource "yandex_compute_instance" "main" {
  name        = "${var.project_name}-vm"
  platform_id = "standard-v2"
  zone        = var.yc_zone

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
    subnet_id          = yandex_vpc_subnet.main.id
    security_group_ids = [yandex_vpc_security_group.main.id]
    nat                = true
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = var.project_name
    env     = "lab"
    managed = "terraform"
  }
}
