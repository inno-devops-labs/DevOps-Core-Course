terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.80"
    }
  }
}

provider "yandex" {
  # Ваш абсолютный путь к ключу
  service_account_key_file = "C:/Users/Bulat/Documents/GitHub/DevOps-Core-Course/terraform/yandex-key.json"
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = var.zone
}

# Сеть и подсеть
resource "yandex_vpc_network" "net" {
  name = "lab-net"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["10.0.0.0/24"]
}

# --- БЛОК SECURITY GROUP УДАЛЕН, ТАК КАК ОН ВЫЗЫВАЛ ОШИБКУ ДОСТУПА ---

# VM
resource "yandex_compute_instance" "vm" {
  name        = "lab-vm"
  platform_id = "standard-v2"
  zone        = var.zone

  resources {
    cores         = 2
    core_fraction = 20
    memory        = 2 # Рекомендуется 2GB для стабильной работы Ubuntu
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true
    # Ссылка на security_group_ids удалена. 
    # Облако автоматически назначит стандартную (default) группу.
  }

  metadata = {
    # Ваш путь к SSH ключу
    ssh-keys = "ubuntu:${file("C:/Users/Bulat/.ssh/id_rsa.pub")}"
  }
}

# Data source — последняя Ubuntu LTS
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# Вывод Public IP
output "vm_ip" {
  value = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}