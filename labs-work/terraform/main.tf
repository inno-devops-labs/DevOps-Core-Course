terraform {
  required_version = ">= 1.5"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.13"
    }
  }
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_vpc_network" "devops" {
  name = "devops-network"

  labels = {
    project = "devops-course"
    lab     = "lab04"
  }
}

resource "yandex_vpc_subnet" "devops" {
  name           = "devops-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.devops.id
  v4_cidr_blocks = ["10.0.1.0/24"]

  labels = {
    project = "devops-course"
    lab     = "lab04"
  }
}

resource "yandex_vpc_security_group" "devops" {
  name       = "devops-sg"
  network_id = yandex_vpc_network.devops.id

  ingress {
    description    = "Allow SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Allow HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Allow app port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  labels = {
    project = "devops-course"
    lab     = "lab04"
  }
}

resource "yandex_compute_instance" "devops" {
  name        = var.instance_name
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
    subnet_id          = yandex_vpc_subnet.devops.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.devops.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = "devops-course"
    lab     = "lab04"
  }
}
