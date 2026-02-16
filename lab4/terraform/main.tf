data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

locals {
  use_existing_network = var.existing_instance_id_for_network != null
}

data "yandex_compute_instance" "network_source" {
  count       = local.use_existing_network ? 1 : 0
  instance_id = var.existing_instance_id_for_network
}

data "yandex_vpc_subnet" "existing" {
  count     = local.use_existing_network ? 1 : 0
  subnet_id = data.yandex_compute_instance.network_source[0].network_interface[0].subnet_id
}

resource "yandex_vpc_network" "lab04" {
  count = local.use_existing_network ? 0 : 1

  name   = var.network_name
  labels = var.resource_labels
}

resource "yandex_vpc_subnet" "lab04" {
  count = local.use_existing_network ? 0 : 1

  name           = var.subnet_name
  zone           = var.zone
  network_id     = yandex_vpc_network.lab04[0].id
  v4_cidr_blocks = [var.subnet_cidr_block]
  labels         = var.resource_labels
}

resource "yandex_vpc_security_group" "lab04" {
  name        = var.security_group_name
  description = "Allow SSH from trusted CIDR, HTTP, and port 5000."
  network_id  = local.use_existing_network ? data.yandex_vpc_subnet.existing[0].network_id : yandex_vpc_network.lab04[0].id

  ingress {
    description    = "SSH from trusted address only"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    description    = "HTTP from anywhere"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "Application port 5000 from anywhere"
    protocol       = "TCP"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description    = "Allow all outbound traffic"
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_vpc_address" "lab04" {
  name = "${var.vm_name}-public-ip"

  external_ipv4_address {
    zone_id = var.zone
  }
}

resource "yandex_compute_instance" "lab04" {
  name                      = var.vm_name
  zone                      = var.zone
  platform_id               = "standard-v2"
  allow_stopping_for_update = true
  labels                    = var.resource_labels

  resources {
    cores         = var.cores
    memory        = var.memory
    core_fraction = var.core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.boot_disk_size
      type     = var.boot_disk_type
    }
  }

  network_interface {
    subnet_id          = local.use_existing_network ? data.yandex_vpc_subnet.existing[0].id : yandex_vpc_subnet.lab04[0].id
    nat                = true
    nat_ip_address     = yandex_vpc_address.lab04.external_ipv4_address[0].address
    security_group_ids = [yandex_vpc_security_group.lab04.id]
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${trimspace(file(var.ssh_public_key_path))}"
  }

  scheduling_policy {
    preemptible = var.preemptible
  }
}
