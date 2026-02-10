# Terraform Infrastructure for DevOps Course

This directory contains Terraform configuration for provisioning cloud infrastructure on Yandex Cloud.

## Prerequisites

1. **Terraform CLI** (version >= 1.9.0)
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

2. **Yandex Cloud CLI** (optional, for getting tokens)
   ```bash
   curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
   ```

3. **SSH Key Pair**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

## Project Structure

```
terraform/
├── .gitignore           # Ignore state and secrets
├── main.tf              # Main resources (VM, network, security group)
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── versions.tf          # Provider versions
├── terraform.tfvars.example  # Example configuration
└── README.md            # This file
```

## Resources Created

- **VPC Network** - Virtual private cloud network
- **Subnet** - Subnet within the VPC
- **Security Group** - Firewall rules:
  - SSH (port 22)
  - HTTP (port 80)
  - HTTPS (port 443)
  - Custom app (port 5000)
  - ICMP (ping)
- **Compute Instance** - Ubuntu 24.04 VM (free tier: 2 cores @ 20%, 1GB RAM)
- **Public IP** - NAT IP for external access

## Quick Start

1. **Copy and configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Get Yandex Cloud credentials:**
   ```bash
   # Login to Yandex Cloud
   yc init

   # Get OAuth token
   yc iam create-token

   # Get Cloud ID
   yc resource-manager cloud list

   # Get Folder ID
   yc resource-manager folder list
   ```

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

4. **Preview changes:**
   ```bash
   terraform plan
   ```

5. **Apply infrastructure:**
   ```bash
   terraform apply
   ```

6. **Connect to VM:**
   ```bash
   # Get SSH command from output
   terraform output ssh_connection_command
   ```

## Destroy Infrastructure

```bash
terraform destroy
```

## Important Notes

- ⚠️ **Never commit `terraform.tfvars` to Git** - it contains secrets
- ⚠️ **Never commit `*.tfstate` files** - they contain sensitive data
- ✅ Use free tier instance settings to avoid costs
- ✅ Run `terraform destroy` when done to avoid charges
- ✅ Keep VM running if you need it for Lab 5 (Ansible)

## Outputs

After `terraform apply`, you'll see:
- `vm_public_ip` - Public IP address for SSH/HTTP access
- `ssh_connection_command` - Ready-to-use SSH command
- `vm_id` - Instance ID for reference
- `network_id`, `subnet_id`, `security_group_id` - Network resource IDs

## Security Best Practices

1. **Restrict SSH access** - Change `allowed_ssh_cidr` to your IP
2. **Use environment variables** - Alternative to terraform.tfvars
3. **Enable audit logging** - Track infrastructure changes
4. **Regular security reviews** - Check security group rules

## Troubleshooting

### SSH Connection Failed
```bash
# Check VM is running
yc compute instance list

# Verify security group allows SSH
yc vpc security-group get <security-group-id>

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

### Terraform Apply Errors
```bash
# Validate configuration
terraform validate

# Check state
terraform state list

# Force unlock if stuck
terraform force-unlock <lock-id>
```
