# Lab 04 — Task 1 (Terraform VM Creation, Yandex Cloud)

## What this creates

- `yandex_vpc_network` and `yandex_vpc_subnet` (or reuses existing subnet/network when `existing_instance_id_for_network` is set)
- `yandex_vpc_security_group` with ingress rules:
  - SSH (22) only from `ssh_allowed_cidr`
  - HTTP (80) from anywhere
  - Port 5000 from anywhere
- `yandex_vpc_address` (public IP)
- `yandex_compute_instance` with free-tier-friendly settings:
  - `platform_id = standard-v2`
  - `cores = 2`, `core_fraction = 20`, `memory = 1`
  - boot disk: `10 GB`, `network-hdd`

## Prerequisites

- Terraform CLI installed
- Yandex Cloud account and permissions
- One authentication method configured:
  - environment variables/YC CLI profile, or
  - `yc_token`, or
  - `service_account_key_file`
- Existing SSH public key (for example `~/.ssh/id_ed25519.pub`)

## Configure variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values.

If your folder has VPC network quota limits, set `existing_instance_id_for_network` to any existing VM ID from the same folder so Terraform can attach the new VM to that existing network/subnet.

## Apply infrastructure

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Verify SSH access

```bash
terraform output ssh_command
# then run command from output, for example:
ssh ubuntu@<public_ip>
```

## Cleanup (when needed)

```bash
terraform destroy
```
