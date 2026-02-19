data "yandex_vpc_network" "default" {
  name = "default"
}

data "yandex_vpc_subnet" "default" {
  name = "default-${var.zone}"
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts-oslogin"
}


resource "yandex_vpc_security_group" "lab_sg" {
  name       = "lab-sg"
  network_id = data.yandex_vpc_network.default.id

  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
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

resource "yandex_compute_instance" "lab_vm" {
  name = "lab-vm"

  platform_id = "standard-v2"

  resources {
    cores         = 2
    core_fraction = 20
    memory        = 1
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
    }
  }

  network_interface {
    subnet_id          = data.yandex_vpc_subnet.default.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
  }

  metadata = {
  ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  ssh_public_key = "${file(var.ssh_public_key_path)}"
}
}