provider "yandex" {
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
  service_account_key_file = var.service_account_key_file
}

resource "yandex_vpc_network" "network" {
  name        = var.network_name
  description = "VPC network for DevOps Lab 04"
  labels      = var.labels
}

resource "yandex_vpc_subnet" "subnet" {
  name           = var.subnet_name
  description    = "Subnet for DevOps Lab 04 VM"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.1.0/24"]
  labels         = var.labels
}

resource "yandex_vpc_security_group" "sg" {
  name        = var.security_group_name
  description = "Security group for DevOps Lab 04 VM - allows SSH, HTTP, and port 5000"
  network_id  = yandex_vpc_network.network.id
  labels      = var.labels

  ingress {
    description    = "SSH access"
    port           = 22
    protocol       = "TCP"
    v4_cidr_blocks = [var.allowed_ssh_ip]
  }

  ingress {
    description    = "HTTP access"
    port           = 80
    protocol       = "TCP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Application port (5000)"
    port           = 5000
    protocol       = "TCP"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  description = var.vm_description
  platform_id = var.vm_platform_id
  zone        = var.zone
  labels      = var.labels

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.vm_disk_size
      type     = var.vm_disk_type
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    security_group_ids = [yandex_vpc_security_group.sg.id]
    nat                = true
  }

  resources {
    cores         = var.vm_cores
    core_fraction = var.vm_core_fraction
    memory        = var.vm_memory
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }

  scheduling_policy {
    preemptible = false
  }
}