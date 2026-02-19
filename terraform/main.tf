data "yandex_compute_image" "ubuntu" {
  family = var.vm_image_family
}

resource "yandex_vpc_network" "network" {
  name = var.network_name
}

resource "yandex_vpc_subnet" "subnet" {
  name           = var.subnet_name
  zone           = var.yandex_zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = [var.subnet_cidr]
}

resource "yandex_vpc_security_group" "sg" {
  name       = "lab04-security-group"
  network_id = yandex_vpc_network.network.id

  ingress {
    description    = "SSH"
    protocol       = "TCP"
    from_port      = 22
    to_port        = 22
    v4_cidr_blocks = [var.my_ip]
  }

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    from_port      = 80
    to_port        = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Custom port 5000"
    protocol       = "TCP"
    from_port      = 5000
    to_port        = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "All outgoing traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  ssh_public_key = file(pathexpand(var.ssh_public_key_path))
}

resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  platform_id = "standard-v2"
  zone        = var.yandex_zone

  resources {
    cores         = var.vm_cores
    core_fraction = var.vm_core_fraction
    memory        = var.vm_memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.vm_disk_size
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${local.ssh_public_key}"
  }

  labels = {
    environment = "lab04"
    managed-by  = "terraform"
  }
}
