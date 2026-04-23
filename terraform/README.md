# Terraform — Yandex Cloud VM

This directory contains Terraform code to provision a virtual machine on **Yandex Cloud** (free‑tier).

## Prerequisites

| Tool | Version |
|------|---------|
| Terraform CLI | ≥ 1.9 |
| Yandex Cloud account | — |
| SSH key pair | `~/.ssh/id_rsa{,.pub}` |

## Quick Start

```bash
# 1. Copy example vars and fill in your credentials
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Yandex Cloud token, cloud/folder IDs

# 2. Initialise providers
terraform init

# 3. Preview changes
terraform plan

# 4. Apply
terraform apply

# 5. Connect
ssh ubuntu@$(terraform output -raw vm_public_ip)
```

## Clean Up

```bash
terraform destroy
```

## File Layout

| File | Purpose |
|------|---------|
| `main.tf` | Provider, data sources, resources |
| `variables.tf` | Input variable declarations |
| `outputs.tf` | Output value definitions |
| `terraform.tfvars.example` | Template for secret variable values |
| `.gitignore` | Ignores state, tfvars, .terraform/ |

## Resources Created

- `yandex_vpc_network` — virtual network
- `yandex_vpc_subnet` — subnet (10.0.1.0/24)
- `yandex_vpc_security_group` — firewall (SSH 22, HTTP 80, App 5000)
- `yandex_compute_instance` — Ubuntu 24.04 LTS VM (2 vCPU @ 20 %, 1 GB RAM, 10 GB HDD)
