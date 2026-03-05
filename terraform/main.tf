terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.120"
    }
  }
  required_version = ">= 1.9.0"
}

provider "yandex" {
  token     = var.token
  zone      = var.zone
  folder_id = var.folder_id
}

resource "yandex_vpc_network" "lab04_network" {
  name        = "lab04-network"
  description = "Network for Lab 04 DevOps VM"
}

resource "yandex_vpc_subnet" "lab04_subnet" {
  name           = "lab04-subnet"
  description    = "Subnet for Lab 04 DevOps VM"
  v4_cidr_blocks = ["10.128.0.0/24"]
  zone           = var.zone
  network_id     = yandex_vpc_network.lab04_network.id
}

resource "yandex_vpc_security_group" "lab04_sg" {
  name        = "lab04-security-group"
  description = "Security group for Lab 04 VM"
  network_id  = yandex_vpc_network.lab04_network.id

  ingress {
    protocol       = "TCP"
    description    = "SSH access"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP access"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  ingress {
    protocol       = "TCP"
    description    = "Custom app port for future deployment"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_compute_instance" "lab04_vm" {
  name        = "lab04-devops-vm"
  description = "VM for Lab 04 - Infrastructure as Code"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
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
    subnet_id          = yandex_vpc_subnet.lab04_subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab04_sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    lab     = "lab04"
    course  = "devops"
    tool    = "terraform"
    purpose = "learning-iac"
  }
}
