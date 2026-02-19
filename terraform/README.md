# Terraform — Yandex Cloud VM

Creates a VM with network, subnet, security group, and public IP on Yandex Cloud.

## Prerequisites

- Terraform >= 1.9.0
- Yandex Cloud account with configured CLI (`yc init`)
- SSH key pair (`ssh-keygen -t rsa -b 4096`)

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

## Connect to VM

```bash
terraform output ssh_command
```

## Resources

| Resource | Type | Details |
|----------|------|---------|
| VPC Network | `yandex_vpc_network` | lab04-network |
| Subnet | `yandex_vpc_subnet` | 10.0.1.0/24, ru-central1-a |
| Security Group | `yandex_vpc_security_group` | SSH(22), HTTP(80), App(5000) |
| VM | `yandex_compute_instance` | 2 vCPU (20%), 1 GB RAM, Ubuntu 24.04, 10 GB HDD |

## Cleanup

```bash
terraform destroy
```
