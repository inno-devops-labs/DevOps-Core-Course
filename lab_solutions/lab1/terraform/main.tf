terraform {
  required_version = ">= 0.13"

  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.85"
    }
  }
}

provider "yandex" {
  service_account_key_file = var.service_account_key_file
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

data "local_file" "public_key" {
  filename = var.public_key_path
}

resource "yandex_vpc_network" "lab_network" {
  name        = "${var.instance_name}-network"
  description = "Network for lab4 vm"

  labels = {
    environment = "lab"
    managed-by  = "terraform"
    purpose     = "devops"
  }
}

resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "${var.instance_name}-subnet"
  description    = "Subnet for lab4 vm in ${var.zone}"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = [var.vpc_cidr]

  labels = {
    environment = "lab"
    managed-by  = "terraform"
  }
}

resource "yandex_vpc_security_group" "lab_sg" {
  name        = "${var.instance_name}-security-group"
  description = "Security group with firewall rules for Lab4 VM"
  network_id  = yandex_vpc_network.lab_network.id

  labels = {
    environment = "lab"
    managed-by  = "terraform"
  }

  ingress {
    description    = "SSH access for remote management"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "HTTP web traffic"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Application port for Docker container"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Lab6 App port 8000"
    protocol       = "TCP"
    port           = 8000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outgoing traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

resource "yandex_compute_instance" "lab_vm" {
  name        = var.instance_name
  description = "Lab4 virtual machine for DevOps"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    auto_delete = true

    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab_subnet.id
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
    nat                = true
  }

  metadata = {
    ssh-keys = "${var.vm_username}:${chomp(data.local_file.public_key.content)}"
  }

  allow_stopping_for_update = true

  labels = {
    environment = "lab"
    managed-by  = "terraform"
    course      = "devops"
    lab         = "04"
  }
}

