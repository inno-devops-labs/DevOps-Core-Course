# Terraform — Lab 04

Provisions an AWS EC2 t2.micro instance (Ubuntu 24.04) with a VPC, subnet, internet gateway, security group, and Elastic IP.

## Prerequisites

- [Terraform >= 1.9](https://developer.hashicorp.com/terraform/downloads)
- AWS account with IAM credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- SSH key pair generated locally

## Usage

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with your values

terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `region` | AWS region | `us-east-1` |
| `instance_type` | EC2 instance type | `t2.micro` |
| `project_name` | Name prefix for all resources | `devops-lab04` |
| `ssh_public_key` | SSH public key content | required |
| `allowed_ssh_cidr` | CIDR allowed for SSH | required |

## terraform.tfvars example

```hcl
ssh_public_key   = "ssh-ed25519 AAAA... user@host"
allowed_ssh_cidr = "203.0.113.1/32"
```

## Outputs

| Output | Description |
|--------|-------------|
| `public_ip` | Elastic IP of the VM |
| `instance_id` | EC2 instance ID |
| `ssh_command` | Ready-to-use SSH command |

## Cleanup

```bash
terraform destroy
```
