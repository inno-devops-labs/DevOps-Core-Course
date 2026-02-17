# Lab 04 Terraform (AWS)

This Terraform configuration provisions:

- VPC + public subnet + internet gateway + route table
- Security group: SSH (22) from your public IP, HTTP (80), app port (5000)
- EC2 instance (Ubuntu 24.04)
- Elastic IP attached to the instance
- EC2 key pair from `terraform/keys/*.pub`

## Prerequisites

- AWS CLI configured (`aws sts get-caller-identity` works)
- Terraform installed

## Run

```bash
cd terraform
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

After apply:

```bash
terraform output public_ip
ssh -i keys/lab04_terraform_key ubuntu@$(terraform output -raw public_ip)
```

## Destroy

```bash
cd terraform
terraform destroy
```
