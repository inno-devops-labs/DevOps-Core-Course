terraform {
  required_version = ">= 1.0"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  zone = var.zone
}

resource "yandex_vpc_network" "lab_network" {
  name        = "${var.project_name}-network"
  description = "Network for Lab 04"
}

resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "${var.project_name}-subnet"
  description    = "Subnet for Lab 04"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["10.128.0.0/24"]
}

resource "yandex_vpc_security_group" "lab_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for Lab 04 VM"
  network_id  = yandex_vpc_network.lab_network.id

  ingress {
    protocol       = "TCP"
    description    = "Allow SSH"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow custom app"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

resource "yandex_compute_instance" "lab_vm" {
  name        = "${var.project_name}-vm"
  hostname    = "${var.project_name}-vm"
  zone        = var.zone
  platform_id = "standard-v2"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab_subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  scheduling_policy {
    preemptible = true
  }

  labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
    lab         = "lab04"
  }
}
