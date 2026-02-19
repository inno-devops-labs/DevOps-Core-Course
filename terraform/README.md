# Terraform — Yandex Cloud VM

## Prerequisites

- Terraform >= 1.9
- Yandex Cloud account with service account key (JSON)
- SSH key pair (`~/.ssh/id_rsa` / `~/.ssh/id_rsa.pub`)

## Setup

1. Create `terraform.tfvars`:

```hcl
cloud_id                 = "your-cloud-id"
folder_id                = "your-folder-id"
zone                     = "ru-central1-a"
service_account_key_file = "~/yc-key.json"
ssh_user                 = "ubuntu"
ssh_public_key_path      = "~/.ssh/id_rsa.pub"
```

2. Run:

```bash
terraform init
terraform plan
terraform apply
```

3. Get VM IP and connect via SSH:

```bash
terraform output vm_public_ip    # or: terraform output ssh_connection
ssh ubuntu@<VM_PUBLIC_IP>
```

## Cleanup

```bash
terraform destroy
```

## Resources Created

| Resource | Description |
|---|---|
| `yandex_vpc_network` | VPC network |
| `yandex_vpc_subnet` | Subnet (10.0.1.0/24) |
| `yandex_vpc_security_group` | Firewall: SSH(22), HTTP(80), App(5000) |
| `yandex_compute_instance` | Ubuntu 24.04 VM (2 vCPU 20%, 2GB RAM, 10GB HDD) |
