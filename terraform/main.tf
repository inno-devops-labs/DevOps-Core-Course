terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  zone = var.zone
}

resource "yandex_vpc_network" "net" {
  name = "lab-net"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "sg" {
  name       = "lab-sg"
  network_id = yandex_vpc_network.net.id

  ingress {
    protocol       = "TCP"
    description    = "SSH from my IP"
    v4_cidr_blocks = [var.my_ip_cidr]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  ingress {
    protocol       = "TCP"
    description    = "App port 5000"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outbound"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "vm" {
  name        = "lab-vm"
  platform_id = var.platform_id

  resources {
    cores         = var.cores
    core_fraction = var.core_fraction
    memory        = var.memory_gb
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      size     = var.boot_disk_gb
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = "lab4"
    iac     = "terraform"
  }
}
