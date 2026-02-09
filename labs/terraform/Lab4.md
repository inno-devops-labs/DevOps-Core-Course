# Task 1 — Terraform VM Creation

## Objective
Create a virtual machine using Terraform on Yandex Cloud provider with complete infrastructure setup including networking, security groups, and public IP address.

---

## Cloud Provider & Setup

### Cloud Provider Chosen: **Yandex Cloud**

**Why Yandex Cloud?**
- Provides free tier resources suitable for learning and testing
- Has a straightforward Terraform provider
- Offers good documentation and regional infrastructure (ru-central1)
- Suitable for deploying containerized applications

### Terraform Version
\`\`\`
Terraform v1.5.7
on darwin_arm64
+ provider registry.terraform.io/yandex-cloud/yandex v0.184.0
\`\`\`

### Authentication Setup
- **Method**: Service Account Key File
- **File**: `authorized_key.json` (added to .gitignore)
- **Configuration**: Service account credentials stored securely, not committed to version control

---

## Infrastructure Configuration

### Resources Created

#### 1. **Virtual Machine (Compute Instance)**
- **Name**: `terraform-vm`
- **Platform**: `standard-v2` (cost-effective, free tier compatible)
- **CPU Cores**: 2 (20% core fraction = shared CPU)
- **Memory**: 2 GB
- **Boot Disk Size**: 10 GB
- **OS Image**: Custom image by `image_id` (Yandex Cloud)
- **Public IP**: Enabled via NAT

#### 2. **Virtual Private Cloud (VPC)**
- **Network Name**: `network-1`
- **Subnet Name**: `subnet1`
- **Region/Zone**: `ru-central1-a`
- **CIDR Block**: `192.168.10.0/24`

#### 3. **Security Configuration**
- **SSH Access**: Enabled from public key (`~/.ssh/yandex_cloud.pub`)
- **Security Groups**: Not defined explicitly in Terraform (uses default VPC behavior)

#### 4. **Public IP Address**
- Automatically assigned via NAT configuration
- Output variable: `external_ip_address_vm_1`

---

## Terraform Configuration Files

### Directory Structure
\`\`\`
terraform/
├── main.tf                 # Main infrastructure code
├── variables.tf            # Variable definitions
├── terraform.tfvars        # Variable values (in .gitignore)
├── authorized_key.json     # Service account key (in .gitignore)
├── .gitignore              # Security best practices
├── Lab4.md                 # This documentation
└── screenshots/            # Evidence of deployment
\`\`\`

### Key Configuration Details

**main.tf**:
\`\`\`terraform
# Provider configuration
provider "yandex" {
  service_account_key_file = "./authorized_key.json"
  cloud_id                 = var.cloud_id
  folder_id                = var.folder_id
  zone                     = "ru-central1-a"
}

# Network resources
resource "yandex_vpc_network" "network-1" { ... }
resource "yandex_vpc_subnet" "subnet1" { ... }

# Compute instance
resource "yandex_compute_instance" "vm-1" {
  name        = "terraform-vm"
  platform_id = "standard-v2"
  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }
  # Network configuration with public IP
  network_interface {
    subnet_id = yandex_vpc_subnet.subnet1.id
    nat       = true
  }
}

# Output public IP
output "external_ip_address_vm_1" {
  value = yandex_compute_instance.vm-1.network_interface.0.nat_ip_address
}
\`\`\`

**variables.tf**:
\`\`\`terraform
variable "cloud_id" {
  type = string
}

variable "folder_id" {
  type = string
}
\`\`\`

**terraform.tfvars** (not committed):
\`\`\`
cloud_id  = "b1g1rs4u1clppvv49r7g"
folder_id = "b1g0u4o89j3n6i6tnd9s"
\`\`\`

---

## Deployment Process

### Step 1: Initialize Terraform
\`\`\`bash
terraform init
\`\`\`
Downloads provider plugins and initializes the working directory.

### Step 2: Validate Configuration
\`\`\`bash
terraform validate
\`\`\`
Ensures configuration syntax is correct.

### Step 3: Review Plan
\`\`\`bash
terraform plan
\`\`\`
Preview all resources that will be created.

### Step 4: Apply Configuration
\`\`\`bash
terraform apply
\`\`\`
Creates the actual infrastructure on Yandex Cloud.

---

## Access Information

### SSH Connection
\`\`\`bash
ssh -i ~/.ssh/yandex_cloud ubuntu@<PUBLIC_IP>
\`\`\`

### Retrieving Public IP
\`\`\`bash
terraform output external_ip_address_vm_1
\`\`\`

### Verification Commands
\`\`\`bash
# Check VM status
terraform show

# List all resources
terraform state list

# Get specific resource details
terraform state show yandex_compute_instance.vm-1
\`\`\`

---

## State Management

### Local State File
- **File**: `terraform.tfstate` (generated locally)
- **Backup**: `terraform.tfstate.backup` (automatic backup)
- **.gitignore**: Both state files are NOT committed to Git

### Why State Files Are Important
- Contains deployed resource information
- Tracks current infrastructure state
- Enables terraform plan to work properly
- **SECURITY**: Contains sensitive data (IPs, IDs), never commit to Git

### State File Location
\`\`\`
.terraform/          # Cached provider plugins (ignored)
.terraform.lock.hcl  # Provider version lock (ignored)
terraform.tfstate    # Current state (ignored)
\`\`\`

---

## Security Best Practices Implemented

✅ **Sensitive Files in .gitignore**:
- `authorized_key.json` - Service account credentials
- `*.tfstate` - Infrastructure state data
- `*.tfvars` - Variable values with credentials
- `.terraform/` - Provider cache

✅ **Infrastructure Security**:
- SSH key-based authentication (no passwords)
- Network isolation with VPC/Subnet
- Public IP restricted to NAT access
- Resource tags for identification

✅ **Terraform Best Practices**:
- Variables for reusable configuration
- Clear resource naming conventions
- Output values for easy reference
- Modular code structure

---

## Evidence of Successful Deployment

### Terraform Plan Output
![Terraform Plan](./screenshots/04-terr-apply.png)

### SSH Connection Proof
![SSH Connection Successful](./screenshots/04-terr-connection.png)

---

## Summary

| Item | Details |
|------|---------|
| **Cloud Provider** | Yandex Cloud (ru-central1-a zone) |
| **VM Name** | terraform-vm |
| **Instance Type** | standard-v2 (2 cores, 2GB RAM, 20% share) |
| **Storage** | 10 GB SSD |
| **Network** | 192.168.10.0/24 subnet in network-1 VPC |
| **Public Access** | NAT enabled |
| **SSH Access** | Ubuntu user with public key authentication |
| **Terraform Version** | 1.5.7 |
| **Provider Version** | yandex-cloud/yandex v0.184.0 |
| **State Management** | Local (terraform.tfstate in .gitignore) |

---

## Cleanup (if needed)
\`\`\`bash
terraform destroy
\`\`\`
This command will remove all created resources from Yandex Cloud.

---

**Status**: ✅ Completed
**Date**: February 9, 2026
**Points**: 4/4
EOF