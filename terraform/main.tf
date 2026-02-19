data "yandex_compute_image" "image" {
  family = "ubuntu-2204-lts"
}

data "yandex_vpc_network" "nw" {
  name = var.vpc_network_name
}



resource "yandex_vpc_subnet" "subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = data.yandex_vpc_network.nw.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}


resource "yandex_compute_instance" "vm" {
  name        = "${var.project_name}-vm"
  platform_id = var.platform
  zone        = var.zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.image.id
      size     = 10
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true
  }

  metadata = {
    ssh-keys = "ubuntu:${file(pathexpand(var.ssh_public_key_path))}"
  }

  labels = {
    project = var.project_name
  }
}
