# Terraform (Lab 04)

This directory contains Terraform configuration to create a small VM in Yandex Cloud.

Quick steps:

1. Install Terraform 1.9+
2. Configure authentication (see docs/LAB04.md)
3. Create `terraform.tfvars` with `folder_id`, `my_ip` (and optionally override `zone`)
4. Run:

```bash
terraform init
terraform fmt
terraform validate
terraform plan -out=plan.out
terraform apply "plan.out"
```

After apply, get the public IP:

```bash
terraform output public_ip
```

To destroy:

```bash
terraform destroy
```
