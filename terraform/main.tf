terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.187"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.9.0"
}

provider "yandex" {
  service_account_key_file = pathexpand(var.service_account_key_file)
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

# Get latest Ubuntu 24.04 image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

# Create VPC network
resource "yandex_vpc_network" "lab04_network" {
  name        = "lab04-network"
  description = "Network for Lab 04 VM"
}

# Create subnet
resource "yandex_vpc_subnet" "lab04_subnet" {
  name           = "lab04-subnet"
  description    = "Subnet for Lab 04 VM"
  v4_cidr_blocks = ["10.128.0.0/24"]
  zone           = var.zone
  network_id     = yandex_vpc_network.lab04_network.id
}

# Create security group with required rules
resource "yandex_vpc_security_group" "lab04_sg" {
  name        = "lab04-sg"
  description = "Lab04 security group"
  network_id  = yandex_vpc_network.lab04_network.id

  ingress {
    protocol       = "TCP"
    description    = "SSH from my IP"
    v4_cidr_blocks = [var.ssh_allowed_cidr]
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
    description    = "App 5000"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all egress"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

# Create VM instance
resource "yandex_compute_instance" "lab04_vm" {
  name        = var.vm_name
  hostname    = var.vm_name
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20 # Free tier: 20% CPU
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10 # 10 GB HDD
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab04_subnet.id
    nat                = true # Assign public IP
    security_group_ids = [yandex_vpc_security_group.lab04_sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    environment = "lab04"
    managed_by  = "terraform"
    purpose     = "devops-course"
  }

  scheduling_policy {
    preemptible = false
  }
}