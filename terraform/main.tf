# Provider init
terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {}

# Actual Ubuntu по family
data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

# Network/VPC
resource "yandex_vpc_network" "net" {
  name = "${var.prefix}-net"
  labels = {
    lab = "lab04"
  }
}

# Subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = "${var.prefix}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = [var.subnet_cidr]
}

# Security Group / Firewall rules
resource "yandex_vpc_security_group" "sg" {
  name       = "${var.prefix}-sg"
  network_id = yandex_vpc_network.net.id

  # SSH for personal ip only IP/32
  ingress {
    protocol       = "TCP"
    description    = "SSH from my IP"
    port           = 22
    v4_cidr_blocks = [var.ssh_allowed_cidr]
  }

  # HTTP 80
  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 5000 
  ingress {
    protocol       = "TCP"
    description    = "App port 5000"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Outgoing traffic
  egress {
    protocol       = "ANY"
    description    = "Allow all egress"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }

  labels = {
    lab = "lab04"
  }
}

# VM / Compute Instance
resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = var.platform_id
  zone        = var.zone

  resources {
    cores         = var.cores
    memory        = var.memory_gb
    core_fraction = var.core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.disk_gb
      type     = var.disk_type
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${trimspace(file(var.ssh_public_key_path))}"
  }

  labels = {
    lab = "lab04"
  }
}
