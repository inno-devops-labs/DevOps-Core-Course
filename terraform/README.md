# Lab 04 - Terraform Infrastructure

This directory contains Terraform configuration for creating a VM in Yandex Cloud for the DevOps course Lab 04.

## Prerequisites

1. **Yandex Cloud Account**: Register at https://cloud.yandex.com/
2. **Terraform**: Installed (v1.5.7+)
3. **SSH Key**: Generated for VM access
4. **Yandex Cloud CLI** (optional but helpful): https://cloud.yandex.com/docs/cli/quickstart

## Yandex Cloud Setup

### 1. Create Service Account

```bash
# Install Yandex Cloud CLI (optional)
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Initialize
yc init

# Create service account
yc iam service-account create --name terraform-sa --description "Service account for Terraform"

# Get service account ID
SERVICE_ACCOUNT_ID=$(yc iam service-account get terraform-sa --format json | jq -r '.id')

# Assign editor role to the service account
yc resource-manager folder add-access-binding <YOUR_FOLDER_ID> \
  --role editor \
  --subject serviceAccount:$SERVICE_ACCOUNT_ID

# Create and download authorized key
yc iam key create \
  --service-account-name terraform-sa \
  --output service-account-key.json \
  --description "Key for Terraform"
```

### 2. Get Required IDs

```bash
# Get Cloud ID
yc config list

# Or get from web console: https://console.cloud.yandex.com/
```

### 3. Configure Terraform

```bash
# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# IMPORTANT: Never commit terraform.tfvars to Git!
```

## Infrastructure Resources

This configuration creates:

- **VPC Network**: `lab04-network`
- **Subnet**: `lab04-subnet` (10.128.0.0/24)
- **Security Group**: Rules for SSH (22), HTTP (80), App (5000)
- **VM Instance**: 
  - Platform: standard-v2
  - CPU: 2 cores @ 20% (free tier)
  - RAM: 1 GB
  - Disk: 10 GB HDD
  - OS: Ubuntu 24.04 LTS
  - Public IP: Yes

## Usage

### Initialize Terraform

```bash
cd terraform/
terraform init
```

### Validate Configuration

```bash
terraform fmt      # Format code
terraform validate # Check syntax
```

### Preview Changes

```bash
terraform plan
```

### Apply Infrastructure

```bash
terraform apply

# Type 'yes' when prompted
```

### Get Outputs

```bash
terraform output
terraform output external_ip
terraform output ssh_connection_string
```

### Connect to VM

```bash
# Get SSH command from output
terraform output -raw ssh_connection_string

# Or manually
ssh -i ~/.ssh/yandex_cloud_key ubuntu@<PUBLIC_IP>
```

### Destroy Infrastructure

```bash
terraform destroy

# Type 'yes' when prompted
```

## File Structure

```
terraform/
├── main.tf                    # Main resources (VM, network, security)
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration (commit this)
├── terraform.tfvars           # Actual values (DO NOT COMMIT)
├── service-account-key.json   # Yandex Cloud credentials (DO NOT COMMIT)
└── README.md                  # This file
```

## Security Notes

### Files to NEVER commit to Git:
- `terraform.tfvars` - Contains sensitive IDs
- `*.tfstate*` - Contains infrastructure state and secrets
- `service-account-key.json` - Yandex Cloud credentials
- `.terraform/` - Provider plugins
- `*.pem`, `*.key` - SSH keys

These are already in `.gitignore`.

## Cost Management

This configuration uses **Yandex Cloud Free Tier**:
- ✅ 1 VM with 20% vCPU, 1 GB RAM (FREE)
- ✅ 10 GB HDD storage (FREE)
- ✅ Network traffic within limits (FREE)

**Always run `terraform destroy` when done testing!**

## Troubleshooting

### Authentication Issues

```bash
# Verify service account key
cat service-account-key.json

# Check if file path in terraform.tfvars is correct
```

### SSH Connection Issues

```bash
# Check if SSH key exists
ls -l ~/.ssh/yandex_cloud_key*

# Set correct permissions
chmod 600 ~/.ssh/yandex_cloud_key

# Test connection with verbose output
ssh -v -i ~/.ssh/yandex_cloud_key ubuntu@<PUBLIC_IP>
```

### Resource Already Exists

```bash
# If you get "already exists" errors, import existing resources
terraform import yandex_vpc_network.lab04_network <NETWORK_ID>

# Or destroy manually in Yandex Cloud Console
```

## Next Steps

After successful VM creation:
1. Verify SSH access
2. Document public IP and connection details
3. Keep VM running for Lab 5 (Ansible) OR
4. Run `terraform destroy` and recreate later

## Resources

- [Yandex Cloud Terraform Provider](https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs)
- [Yandex Cloud Documentation](https://cloud.yandex.com/docs)
- [Terraform Documentation](https://www.terraform.io/docs)
