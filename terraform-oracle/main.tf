terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

# Provider configuration
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Get list of availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Get the latest Oracle Linux image
data "oci_core_images" "oracle_linux" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Create VCN (Virtual Cloud Network)
resource "oci_core_vcn" "lab04_vcn" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "lab04-vcn"
  dns_label      = "lab04vcn"
}

# Create Internet Gateway
resource "oci_core_internet_gateway" "lab04_ig" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.lab04_vcn.id
  display_name   = "lab04-internet-gateway"
  enabled        = true
}

# Create Route Table
resource "oci_core_route_table" "lab04_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.lab04_vcn.id
  display_name   = "lab04-route-table"

  route_rules {
    network_entity_id = oci_core_internet_gateway.lab04_ig.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

# Create Security List
resource "oci_core_security_list" "lab04_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.lab04_vcn.id
  display_name   = "lab04-security-list"

  # Allow SSH
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow HTTP
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 80
      max = 80
    }
  }

  # Allow port 5000 for app
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    tcp_options {
      min = 5000
      max = 5000
    }
  }

  # Allow ICMP (ping)
  ingress_security_rules {
    protocol    = "1" # ICMP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
  }

  # Allow all outbound traffic
  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
  }
}

# Create Subnet
resource "oci_core_subnet" "lab04_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.lab04_vcn.id
  cidr_block                 = "10.0.1.0/24"
  display_name               = "lab04-subnet"
  dns_label                  = "lab04subnet"
  route_table_id             = oci_core_route_table.lab04_rt.id
  security_list_ids          = [oci_core_security_list.lab04_sl.id]
  prohibit_public_ip_on_vnic = false
}

# Create Compute Instance (Free Tier - VM.Standard.E2.1.Micro)
resource "oci_core_instance" "lab04_vm" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "lab04-devops-vm"
  shape               = "VM.Standard.E2.1.Micro" # Always Free Tier

  # Shape config (1 OCPU, 1GB RAM for free tier)
  shape_config {
    memory_in_gbs = 1
    ocpus         = 1
  }

  # Create boot volume
  source_details {
    source_id               = data.oci_core_images.oracle_linux.images[0].id
    source_type             = "image"
    boot_volume_size_in_gbs = 50 # Free tier allows up to 200GB total
  }

  # Network configuration
  create_vnic_details {
    subnet_id        = oci_core_subnet.lab04_subnet.id
    display_name     = "lab04-vnic"
    assign_public_ip = true
    hostname_label   = "lab04vm"
  }

  # SSH key and cloud-init
  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data = base64encode(<<-EOF
      #cloud-config
      users:
        - name: ${var.ssh_user}
          groups: sudo
          shell: /bin/bash
          sudo: ['ALL=(ALL) NOPASSWD:ALL']
          ssh-authorized-keys:
            - ${file(var.ssh_public_key_path)}
      package_update: true
      package_upgrade: true
      packages:
        - curl
        - wget
        - git
        - htop
      runcmd:
        - echo "Lab04 DevOps VM initialized" > /home/${var.ssh_user}/welcome.txt
    EOF
    )
  }

  # Tags
  freeform_tags = {
    "Environment" = "lab04"
    "Course"      = "devops"
    "CreatedBy"   = "terraform"
  }
}
