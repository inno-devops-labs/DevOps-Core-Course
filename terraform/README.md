# Terraform Infrastructure for Lab 04

This directory contains Terraform configuration to provision a VM on Yandex Cloud for the DevOps course.

## Prerequisites

1. **Terraform CLI**: Install from https://developer.hashicorp.com/terraform/downloads
2. **Yandex Cloud Account**: Sign up at https://cloud.yandex.com/
3. **Yandex Cloud CLI**: Install from https://cloud.yandex.com/en/docs/cli/quickstart

## Setup Instructions

### 1. Configure Yandex Cloud Authentication

```bash
# Initialize Yandex Cloud CLI
yc init

# Create a service account (if you don't have one)
yc iam service-account create --name terraform-sa

# Get your folder ID
yc config list

# Grant editor role to service account
yc resource-manager folder add-access-binding <folder-id> \
  --role editor \
  --subject serviceAccount:<service-account-id>

# Create authorized key
yc iam key create \
  --service-account-name terraform-sa \
  --output key.json

# Set environment variable for authentication
export YC_SERVICE_ACCOUNT_KEY_FILE="$(pwd)/key.json"
```

### 2. Configure Variables

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# - folder_id: Your Yandex Cloud folder ID
# - my_ip_cidr: Your IP address in CIDR format (e.g., "1.2.3.4/32")

# Get your public IP
curl ifconfig.me
```

### 3. Initialize and Apply

```bash
# Initialize Terraform (download providers)
terraform init

# Format code
terraform fmt

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply infrastructure
terraform apply

# View outputs
terraform output
```

### 4. Connect to VM

```bash
# Use the SSH command from output
ssh -i ~/.ssh/test_vm vglon@<public-ip>

# Or get it with:
terraform output ssh_connection_command
```

## Resources Created

- **VPC Network**: Virtual private cloud network
- **Subnet**: 10.128.0.0/24 subnet in ru-central1-a zone
- **Security Group**: Firewall rules for SSH (22), HTTP (80), and port 5000
- **Compute Instance**: 
  - Platform: standard-v2
  - Cores: 2 (20% core fraction - free tier)
  - Memory: 1 GB
  - Disk: 10 GB HDD
  - OS: Ubuntu 24.04 LTS

## Cleanup

```bash
# Destroy all resources
terraform destroy

# Confirm with 'yes'
```

## Files

- `main.tf`: Main infrastructure resources
- `variables.tf`: Input variable definitions
- `outputs.tf`: Output values
- `terraform.tfvars`: Variable values (gitignored, not committed)
- `terraform.tfvars.example`: Example variable file
- `.terraform/`: Provider plugins (gitignored)
- `terraform.tfstate`: State file tracking real infrastructure (gitignored)

## Security Notes

⚠️ **Never commit these files to Git:**
- `terraform.tfvars` (contains your folder ID and potentially secrets)
- `terraform.tfstate` (contains resource details and metadata)
- `key.json` (service account credentials)
- `.terraform/` directory

✅ These are in `.gitignore` and safe to commit:
- `*.tf` files (configuration code)
- `terraform.tfvars.example` (template without real values)
- `README.md` (this file)

## Cost

This configuration uses Yandex Cloud free tier resources:
- 20% vCPU (2 cores at 20% = 0.4 vCPU)
- 1 GB RAM
- 10 GB HDD

**Expected cost: $0/month** (within free tier limits)

## Troubleshooting

**Authentication Error:**
```bash
# Verify service account key is set
echo $YC_SERVICE_ACCOUNT_KEY_FILE

# Or set it manually
export YC_SERVICE_ACCOUNT_KEY_FILE="/path/to/key.json"
```

**SSH Connection Failed:**
- Check security group allows your IP
- Verify public key is correct: `cat ~/.ssh/test_vm.pub`
- Check VM is running: `terraform show | grep nat_ip_address`

**Resource Already Exists:**
- Terraform tracks state in `terraform.tfstate`
- If you deleted resources manually, use: `terraform refresh`
- Or import existing resources: `terraform import`

## Next Steps

This VM will be used in Lab 5 (Ansible) for configuration management. You have two options:

1. **Keep this VM running** until Lab 5 completion
2. **Destroy it** and recreate later with `terraform apply`

The benefit of Infrastructure as Code: you can recreate identical infrastructure anytime!
