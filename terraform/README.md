# Terraform Infrastructure for Lab 4

This directory contains Terraform configuration for provisioning a virtual machine on Yandex Cloud.

## Prerequisites

- Terraform 1.9+ installed
- Yandex Cloud account
- Service account with appropriate permissions
- Service account key file (`key.json`) - **NOT committed to Git**

## Project Structure

```
terraform/
├── main.tf              # Main infrastructure resources
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── .gitignore          # Git ignore rules
├── key.json            # Service account key (gitignored)
└── docs/
    └── LAB04.md        # Lab documentation
```

## Quick Start

1. **Configure Service Account Key:**
   ```bash
   # Place your Yandex Cloud service account key as key.json
   # This file is gitignored - never commit it!
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review Changes:**
   ```bash
   terraform plan
   ```

4. **Apply Infrastructure:**
   ```bash
   terraform apply
   ```

5. **Get Outputs:**
   ```bash
   terraform output
   ```

6. **Connect to VM:**
   ```bash
   ssh ubuntu@$(terraform output -raw public_ip)
   ```

7. **Destroy Infrastructure:**
   ```bash
   terraform destroy
   ```

## Resources Created

- **VPC Network:** `lab4-network`
- **Subnet:** `lab4-subnet` (192.168.10.0/24)
- **Security Group:** `lab4-security-group`
  - SSH (22)
  - HTTP (80)
  - Custom port (5000)
- **VM Instance:** `lab4-vm`
  - 2 cores (20% fraction)
  - 1 GB RAM
  - 10 GB disk
  - Ubuntu 24.04 LTS

## Variables

- `folder_id` - Yandex Cloud Folder ID (default: provided)
- `zone` - Availability zone (default: ru-central1-a)
- `instance_name` - VM instance name (default: lab4-vm)

## Outputs

- `public_ip` - VM public IP address
- `ssh_command` - Ready-to-use SSH command
- `instance_id` - VM instance ID

## Security Notes

⚠️ **Important:**
- Service account key (`key.json`) is gitignored
- State files (`*.tfstate`) are gitignored
- Security group allows SSH from 0.0.0.0/0 (restrict in production!)
- Never commit credentials or state files

## Documentation

See `docs/LAB04.md` for complete lab documentation.

