# Terraform — Yandex Cloud VM

Infrastructure as Code for Lab 4 using Terraform with Yandex Cloud.

## Resources Created

| Resource | Type | Description |
|----------|------|-------------|
| `lab04-network` | VPC Network | Virtual private cloud |
| `lab04-subnet` | VPC Subnet | Subnet (10.0.1.0/24) |
| `lab04-sg` | Security Group | Firewall rules (SSH, HTTP, 5000) |
| `lab04-vm` | Compute Instance | Ubuntu 24.04 LTS, 2 cores @ 20%, 1 GB RAM |

## Quick Start

```bash
# 1. Copy and fill in your credentials
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Initialize
terraform init

# 3. Preview
terraform plan

# 4. Apply
terraform apply

# 5. Connect
ssh ubuntu@<OUTPUT_IP>

# 6. Destroy when done
terraform destroy
```

## Requirements

- Terraform >= 1.9.0
- Yandex Cloud account
- SSH key pair (`~/.ssh/id_rsa` / `~/.ssh/id_rsa.pub`)
