resource "yandex_vpc_network" "net" {
  name = "lab04-net"
}

resource "yandex_vpc_subnet" "subnet" {
  name           = "lab04-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}

resource "yandex_vpc_security_group" "sg" {
  name       = "lab04-sg"
  network_id = yandex_vpc_network.net.id

  ingress {
    protocol       = "TCP"
    description    = "SSH from my IP"
    port           = 22
    v4_cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App 5000"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outbound"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2404-lts"
}

resource "yandex_compute_instance" "vm" {
  name = var.vm_name
  zone = var.zone

  resources {
    cores         = 2
    core_fraction = 20
    memory        = 2
  }



  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.sg.id]
  }

  metadata = {
    "ssh-keys" = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }
}
