data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

resource "yandex_vpc_network" "net-1" {
  name = "net"
}

resource "yandex_vpc_subnet" "subnet-1" {
  name       = "subnet"
  zone       = "ru-central1-a"
  network_id = yandex_vpc_network.net-1.id
  v4_cidr_blocks = ["10.0.0.0/24"]
}


resource "yandex_vpc_security_group" "sg1" {
  network_id = yandex_vpc_network.net-1.id

  labels = {
    my-label = "my-label-value"
  }

  ingress {
    protocol    = "TCP"
    description = "rule1 description"
    v4_cidr_blocks = ["10.0.1.0/24", "10.0.2.0/24"]
    port        = 8080
  }

  ingress {
    protocol    = "ANY"
    description = "SSH"
    v4_cidr_blocks = ["${var.my_ip}/32"]
    port        = 22
  }

  ingress {
    protocol    = "ANY"
    description = "HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port        = 80
  }

  ingress {
    protocol    = "TCP"
    description = "App 5000"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port        = 5000
  }

  egress {
    protocol = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

}


resource "yandex_compute_instance" "vm-1" {
  name        = "terraform1"
  platform_id = var.instance_platform
  zone        = var.zone

  resources {
    cores  = var.instance_cores
    memory = var.instance_memory
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
    }
  }

  network_interface {
    nat                = true
    subnet_id          = yandex_vpc_subnet.subnet-1.id
    security_group_ids = [yandex_vpc_security_group.sg1.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  labels = {
    environment = "dev"
    project     = "terraform-lab"
  }
}
