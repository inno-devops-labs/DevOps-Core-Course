terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Firewall rules: SSH (22), HTTP (80), app port (5000)
resource "google_compute_firewall" "allow_ssh_http" {
  name    = "lab04-vm-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "5000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["lab04-vm"]
}

# VM instance (e2-micro free tier)
resource "google_compute_instance" "vm" {
  name         = "lab04-vm"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["lab04-vm"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 10
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
    ssh-keys = "ubuntu:${file(var.ssh_public_key_path)}"
  }

  labels = {
    lab = "lab04"
  }
}
