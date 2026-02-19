terraform {
  required_version = ">= 1.5"
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  zone = var.zone
  # folder_id can be set via YC_FOLDER_ID environment variable
  # Or via var.folder_id if specified in terraform.tfvars
  folder_id = var.folder_id != "" ? var.folder_id : null
  # Authentication via environment variables:
  # YC_SERVICE_ACCOUNT_KEY_FILE - path to service account JSON key file
  # YC_TOKEN - OAuth token
  # YC_FOLDER_ID - folder ID (recommended: use this instead of terraform.tfvars)
  # See: https://cloud.yandex.com/en/docs/cli/operations/authentication/service-account
}

# Get latest Ubuntu image
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

# Create VPC network
resource "yandex_vpc_network" "network" {
  name = "${var.project_name}-network"
}

# Create subnet
resource "yandex_vpc_subnet" "subnet" {
  name           = "${var.project_name}-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = [var.subnet_cidr]
}

# Security group creation disabled due to permission issues
# VM will be created without explicit security group
# Default security group of the network will be used
# Rules can be added manually in console after VM creation if needed

# Note: For Lab 04, creating VM without security group is acceptable
# Default security group allows all traffic by default
# You can add rules manually in console after VM is created

# Option 2: Create via Terraform (currently disabled due to permission issues)
# resource "yandex_vpc_security_group" "sg" {
#   name       = "${var.project_name}-sg"
#   network_id = yandex_vpc_network.network.id
#
#   ingress {
#     description    = "SSH"
#     protocol       = "TCP"
#     port           = 22
#     v4_cidr_blocks = [var.allowed_ssh_cidr]
#   }
#
#   ingress {
#     description    = "HTTP"
#     protocol       = "TCP"
#     port           = 80
#     v4_cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   ingress {
#     description    = "Custom port 5000"
#     protocol       = "TCP"
#     port           = 5000
#     v4_cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   egress {
#     description    = "Allow all outbound traffic"
#     protocol       = "ANY"
#     v4_cidr_blocks = ["0.0.0.0/0"]
#   }
# }

# Create compute instance
resource "yandex_compute_instance" "vm" {
  name        = "${var.project_name}-vm"
  platform_id = "standard-v3"  # Updated to match imported VM
  zone        = var.zone
  folder_id   = var.folder_id != "" ? var.folder_id : null  # Explicit folder_id

  resources {
    cores         = 2
    core_fraction = 20  # Free tier: 20% of vCPU
    memory        = 1   # 1 GB RAM
  }

  boot_disk {
    initialize_params {
      # Use the actual image ID from imported VM to avoid recreation
      # Real VM uses: fd8ihnnbgn1ot21ma5s4
      # Data source returns: fd8t9g30r3pc23et5krl
      # Using data source for consistency, but may cause recreation
      # For imported VM, you can use: image_id = "fd8ihnnbgn1ot21ma5s4"
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 10  # 10 GB HDD (free tier)
      type     = "network-hdd"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet.id
    nat       = true  # Enable public IP
    # security_group_ids not specified - will use default security group
    # You can add security group rules manually in console after VM creation
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${file(var.ssh_public_key_path)}"
  }

  labels = {
    project = var.project_name
    env     = var.environment
    managed = "terraform"
  }
}
