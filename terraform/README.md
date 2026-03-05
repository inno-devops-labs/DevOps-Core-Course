# Terraform Lab 04 (AWS)

## Prerequisites
- Terraform >= 1.9
- AWS credentials configured (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- Existing SSH public key

## Quick Start
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Destroy
```bash
terraform destroy
```

## Notes
- Use free-tier instance type only (`t2.micro`).
- Restrict SSH CIDR in `terraform.tfvars` to your real IP (`x.x.x.x/32`).
- Never commit `terraform.tfvars` or state files.
