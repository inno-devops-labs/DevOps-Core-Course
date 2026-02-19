terraform {
  required_version = ">= 1.5.0"

  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.yc_service_account_key_file
  cloud_id                 = var.yc_cloud_id
  folder_id                = var.yc_folder_id
  zone                     = var.yc_zone
}

# --- Network ---

resource "yandex_vpc_network" "lab04" {
  name = "lab04-network"

  labels = {
    project = "devops-lab04"
  }
}

resource "yandex_vpc_subnet" "lab04" {
  name           = "lab04-subnet"
  zone           = var.yc_zone
  network_id     = yandex_vpc_network.lab04.id
  v4_cidr_blocks = ["10.0.1.0/24"]

  labels = {
    project = "devops-lab04"
  }
}

# --- Security Group ---

resource "yandex_vpc_security_group" "lab04" {
  name       = "lab04-sg"
  network_id = yandex_vpc_network.lab04.id

  ingress {
    description    = "SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "App port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  labels = {
    project = "devops-lab04"
  }
}

# --- Compute Instance ---

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_compute_instance" "lab04" {
  name        = "lab04-vm"
  platform_id = "standard-v2"
  zone        = var.yc_zone

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
    subnet_id          = yandex_vpc_subnet.lab04.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab04.id]
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${var.ssh_public_key}"
  }

  labels = {
    project = "devops-lab04"
    env     = "dev"
  }
}
