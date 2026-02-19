# Provider configuration
# Auth: set yandex_cloud_id, yandex_folder_id, yandex_service_account_key_file (or TF_VAR_* / env in script)
provider "yandex" {
  zone                     = var.zone
  cloud_id                 = var.yandex_cloud_id != "" ? var.yandex_cloud_id : null
  folder_id                = var.yandex_folder_id != "" ? var.yandex_folder_id : null
  service_account_key_file = var.yandex_service_account_key_file != "" ? var.yandex_service_account_key_file : null
}

# Data source to get latest Ubuntu image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# VPC Network
resource "yandex_vpc_network" "network" {
  name = "${var.project_name}-network"
}

# Subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = [var.subnet_cidr]
}

# Security Group
resource "yandex_vpc_security_group" "sg" {
  name       = "${var.project_name}-sg"
  network_id = yandex_vpc_network.network.id

  # Allow SSH from your IP
  ingress {
    description    = "SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.ssh_allowed_cidr]
  }

  # Allow HTTP
  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow custom port 5000 for app deployment
  ingress {
    description    = "App port"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    description    = "All outbound"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Compute Instance (VM)
resource "yandex_compute_instance" "vm" {
  name        = "${var.project_name}-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    core_fraction = 20 # Free tier: 20% of 2 cores = 0.4 vCPU
    memory        = 1  # 1 GB RAM (free tier)
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10 # 10 GB (free tier)
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true # Public IP
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  # SSH key for access
  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = var.project_name
    env     = var.environment
    managed = "terraform"
  }
}
