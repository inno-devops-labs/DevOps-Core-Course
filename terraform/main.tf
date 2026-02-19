terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = "key.json"
  folder_id                = "b1g6i74v9cpdj1iolnha"
  zone                     = "ru-central1-a"
}

# Create VPC network
resource "yandex_vpc_network" "network" {
  name = "lab4-network"
}

# Create subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = "lab4-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}

# Create security group
resource "yandex_vpc_security_group" "sg" {
  name       = "lab4-security-group"
  network_id = yandex_vpc_network.network.id

  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"] # In production, restrict to your IP!
  }

  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create VM instance
resource "yandex_compute_instance" "vm" {
  name = "lab4-vm"

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20 # Free tier uses 20% CPU
  }

  boot_disk {
    initialize_params {
      image_id = "fd83ica41cade1mj35sr" # ubuntu 24.04
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true # Get public IP
  }

  metadata = {
    ssh-keys = "ubuntu:${file("~/.ssh/id_ed25519.pub")}" #
  }
}

