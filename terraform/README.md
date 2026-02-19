# Terraform Infrastructure for Lab 4

This directory contains Terraform configuration to provision infrastructure in Yandex Cloud.

## Quick Start

1. **Setup credentials** (see `SETUP.md` for details):
   ```bash
   export YANDEX_CLOUD_ID="your-cloud-id"
   export YANDEX_FOLDER_ID="your-folder-id"
   export YANDEX_SERVICE_ACCOUNT_KEY_FILE="$HOME/.yandex/key.json"
   ```

2. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize and apply**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Connect to VM**:
   ```bash
   terraform output ssh_command
   # Or use the IP directly
   ssh ubuntu@$(terraform output -raw vm_public_ip)
   ```

5. **Destroy when done**:
   ```bash
   terraform destroy
   ```

## Files

- `main.tf` - Main infrastructure resources (VM, network, security group)
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output values (IPs, connection info)
- `versions.tf` - Terraform and provider version constraints
- `terraform.tfvars.example` - Example variable values (copy to `terraform.tfvars`)
- `SETUP.md` - Detailed setup instructions
- `.gitignore` - Ignores state files and credentials

## Resources Created

- **VPC Network** - Isolated network for VM
- **Subnet** - Subnet in specified zone
- **Security Group** - Firewall rules (SSH, HTTP, port 5000)
- **Compute Instance** - Ubuntu 22.04 VM with public IP

## Security Notes

- `terraform.tfvars` is gitignored - never commit it!
- State files (`.tfstate`) are gitignored
- SSH access restricted to your IP (configure in `terraform.tfvars`)
- Credentials via environment variables, not hardcoded

## Documentation

See `SETUP.md` for detailed setup instructions and troubleshooting.
