terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}

provider "yandex" {
  service_account_key_file = "/home/vboxuser/.yc/terraform-key.json"
  cloud_id  = "b1g0qsmtu1cheeq79i0d"
  folder_id = "b1g1cmmbss046n25oln3"
  zone      = "ru-central1-a"
}
resource "yandex_vpc_network" "lab_network" {
  name = "lab-network"
}

resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "lab-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}

resource "yandex_compute_instance" "lab_vm" {
  name        = "lab-vm"
  zone        = "ru-central1-a"
  platform_id = "standard-v2"

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = "fd80bm0rh4rkepi5ksdi" # Ubuntu 24.04 LTS
      size     = 10
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.lab_subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${file("/home/vboxuser/.ssh/id_ed25519.pub")}"
  }
}

output "external_ip" {
  value = yandex_compute_instance.lab_vm.network_interface.0.nat_ip_address
}
