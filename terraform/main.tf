terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone      = var.zone
  folder_id = var.folder_id
  cloud_id  = var.cloud_id
  service_account_key_file = "/home/bulatgazizov/terraform-sa-key.json"
}

resource "yandex_vpc_network" "network" {
  name = "${var.project_name}-network"
  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = [var.subnet_cidr]
  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }
}

resource "yandex_compute_instance" "vm" {
  name     = "${var.project_name}-vm"
  zone     = var.zone
  hostname = "${var.project_name}-vm"

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  resources {
    cores         = var.vm_cores
    memory        = var.vm_memory
    core_fraction = var.vm_core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      size     = var.disk_size
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys  = "ubuntu:${file(var.ssh_public_key_path)}"
    user-data = <<-EOF
      #cloud-config
      runcmd:
        - iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        - iptables -A INPUT -i lo -j ACCEPT
        - iptables -A INPUT -p tcp --dport 22 -s ${var.my_ip}/32 -j ACCEPT
        - iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        - iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
        - iptables -A INPUT -j DROP
        - apt-get install -y iptables-persistent
        - netfilter-persistent save
    EOF
  }
}
