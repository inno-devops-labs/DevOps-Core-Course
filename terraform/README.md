# Terraform — Lab 4 IaC

Provisions a single EC2 VM on AWS (free tier) with SSH, HTTP, and port 5000 open.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.9
- AWS CLI configured, or env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- SSH key pair (default: `~/.ssh/id_rsa.pub`)

## Usage

```bash
cd terraform

# Copy example tfvars (optional)
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values (do not commit!)

terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

## Outputs

- `public_ip` — VM public IP
- `ssh_command` — Example SSH command (user: `ubuntu`)

## Cleanup

```bash
terraform destroy
```

## Security

- Restrict `allowed_ssh_cidr` to your IP (e.g. `"YOUR_IP/32"`).
- Never commit `terraform.tfvars` or `.tfstate`.
