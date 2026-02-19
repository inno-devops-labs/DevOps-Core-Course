# Data source for latest Ubuntu image
data "yandex_compute_image" "ubuntu" {
  family = var.image_family
}

# VPC Network
resource "yandex_vpc_network" "network" {
  name        = var.network_name
  description = "Network for Lab 4 VM"
  labels      = var.labels
}

# Subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = var.subnet_name
  description    = "Subnet for Lab 4 VM"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = var.v4_cidr_blocks
  labels         = var.labels
}

# Security Group
resource "yandex_vpc_security_group" "sg" {
  name        = "lab4-security-group"
  description = "Security group for Lab 4 VM"
  network_id  = yandex_vpc_network.network.id
  labels      = var.labels

  # SSH access
  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = var.allowed_ssh_ips
  }

  # HTTP access
  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 5000 for future app
  ingress {
    protocol       = "TCP"
    description    = "Custom App Port"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outgoing traffic
  egress {
    protocol       = "ANY"
    description    = "Outbound"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}

# Compute Instance - Note: VM gets public IP automatically with nat=true
# We don't need a separate yandex_vpc_address resource for the VM
resource "yandex_compute_instance" "vm" {
  name        = var.vm_name
  description = "VM for Lab 4 - Infrastructure as Code"
  platform_id = var.vm_platform
  zone        = var.zone
  labels      = var.labels

  resources {
    cores         = var.vm_cores
    memory        = var.vm_memory
    core_fraction = var.vm_core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = var.disk_size
      type     = "network-hdd"  # Cheaper for learning
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet.id
    security_group_ids = [yandex_vpc_security_group.sg.id]
    nat                = true  # Automatically assigns public IP
    nat_ip_address     = yandex_vpc_address.static_ip[0].external_ipv4_address[0].address
  }

  metadata = {
    user-data = <<-EOF
      #cloud-config
      users:
        - name: ubuntu
          sudo: ['ALL=(ALL) NOPASSWD:ALL']
          groups: sudo
          shell: /bin/bash
          ssh-authorized-keys:
            - ${var.ssh_public_key}
      packages:
        - curl
        - wget
        - git
        - htop
        - docker.io
      package_update: true
      package_upgrade: false
      runcmd:
        - systemctl enable docker
        - systemctl start docker
        - usermod -aG docker ubuntu
        - echo "Lab 4 VM ready for Ansible Lab 5!" > /etc/motd
    EOF
  }
}

# Create a static public IP address (optional - if you want a static IP)
resource "yandex_vpc_address" "static_ip" {
  count = 1  # Set to 0 if you don't need a static IP
  
  name = "lab4-static-ip"
  
  external_ipv4_address {
    zone_id = var.zone  # This is a string, not a list
  }
}