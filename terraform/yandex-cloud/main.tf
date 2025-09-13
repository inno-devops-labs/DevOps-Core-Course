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
  token     = var.iam_token
  cloud_id  = var.cloud_id
  folder_id = var.folder_id
}

resource "yandex_vpc_network" "network" {
  name = "Network"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "Subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["192.168.0.0/16"]
}

resource "yandex_compute_instance" "vm" {
  name = var.vm_name

  resources {
    memory = var.vm_ram_gb
    cores  = var.vm_cpu_cores
  }

  boot_disk {
    initialize_params {
      image_id = var.vm_image_id
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys = format("%s:%s", var.vm_username, file(var.ssh_pubkey_path))
  }
}
