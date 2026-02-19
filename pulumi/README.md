# Pulumi Infrastructure for DevOps Course

This directory contains Pulumi configuration (Python) for provisioning cloud infrastructure on Yandex Cloud.

## Overview

This Pulumi project creates the **same infrastructure** as the Terraform configuration, demonstrating the differences between declarative (Terraform/HCL) and imperative (Pulumi/Python) IaC approaches.

## Prerequisites

1. **Pulumi CLI** (version >= 3.x)
   ```bash
   # macOS
   brew install pulumi

   # Linux
   curl -fsSL https://get.pulumi.com | sh

   # Windows
   choco install pulumi
   ```

2. **Python 3.8+** (recommended: 3.10-3.13)
   ```bash
   python3 --version
   ```
   > Note: `pulumi-yandex` currently depends on `pkg_resources`, so `requirements.txt` pins `setuptools<81` for compatibility.

3. **Yandex Cloud CLI** (optional, for getting credentials)
   ```bash
   curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
   ```

4. **SSH Key Pair**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   ```

## Project Structure

```
pulumi/
├── .gitignore           # Ignore venv, secrets, state
├── __main__.py          # Main infrastructure code (Python)
├── requirements.txt     # Python dependencies
├── Pulumi.yaml          # Project metadata
├── Pulumi.dev.yaml      # Stack configuration (gitignored!)
└── README.md            # This file
```

## Resources Created

Same as Terraform:
- **VPC Network** - Virtual private cloud network
- **Subnet** - Subnet within the VPC
- **Security Group** - Firewall rules (SSH, HTTP, HTTPS, 5000)
- **Compute Instance** - Ubuntu 24.04 VM (free tier)
- **Public IP** - NAT IP for external access

## Quick Start

1. **Create and activate Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Login to Pulumi:**
   ```bash
   # Use Pulumi Cloud (free tier)
   pulumi login

   # Or use local backend
   pulumi login --local
   ```
   For non-interactive shells, set passphrase first:
   ```bash
   export PULUMI_CONFIG_PASSPHRASE="your-strong-passphrase"
   ```

4. **Create a stack:**
   ```bash
   pulumi stack init dev
   ```

5. **Configure Yandex Cloud credentials:**
   ```bash
   # Set Yandex Cloud credentials
   pulumi config set yandex:token YOUR_YC_TOKEN --secret
   pulumi config set yandex:cloudId YOUR_CLOUD_ID
   pulumi config set yandex:folderId YOUR_FOLDER_ID
   pulumi config set yandex:zone ru-central1-a

   # Set SSH public key
   pulumi config set ssh_public_key "$(cat ~/.ssh/id_rsa.pub)"

   # Required when enable_security_group=true:
   # restrict SSH only to your public IP (/32)
   pulumi config set --path allowed_ssh_cidr[0] "YOUR_PUBLIC_IP/32"
   pulumi config set --path allowed_ingress_cidr[0] "0.0.0.0/0"
   ```

6. **Preview changes:**
   ```bash
   pulumi preview
   ```

7. **Apply infrastructure:**
   ```bash
   pulumi up
   ```

8. **Get outputs:**
   ```bash
   pulumi stack output
   pulumi stack output ssh_connection_command
   ```

## Destroy Infrastructure

```bash
pulumi destroy
```

## Configuration Options

| Config Key | Description | Default |
|------------|-------------|---------|
| `vm_name` | VM instance name | `devops-vm-pulumi` |
| `vm_cores` | Number of CPU cores | `2` |
| `vm_core_fraction` | CPU core fraction (%) | `20` |
| `vm_memory` | RAM in GB | `1` |
| `vm_disk_size` | Disk size in GB | `10` |
| `vm_user` | SSH username | `ubuntu` |
| `ssh_public_key` | SSH public key content | (required) |
| `allowed_ssh_cidr` | CIDR list for SSH access (your public IP/32) | (required when SG enabled) |
| `allowed_ingress_cidr` | CIDR list for HTTP/HTTPS/5000/ICMP | `["0.0.0.0/0"]` |
| `enable_security_group` | Create and attach custom security group | `true` |

Set configuration:
```bash
pulumi config set vm_name my-custom-vm
pulumi config set vm_memory 2
# Use your real public IP in /32 format (required for SSH rule)
pulumi config set --path allowed_ssh_cidr[0] "203.0.113.10/32"
pulumi config set --path allowed_ingress_cidr[0] "0.0.0.0/0"
pulumi config set enable_security_group true
```

## Terraform vs Pulumi Comparison

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Language** | HCL (declarative) | Python (imperative) |
| **State** | Local/Remote file | Pulumi Cloud or local |
| **IDE Support** | Limited | Full (autocomplete, types) |
| **Logic** | count, for_each | Native Python loops/conditions |
| **Testing** | External tools | pytest, unittest |
| **Secrets** | Plain in state | Encrypted by default |

## Key Differences in Code

**Terraform (HCL):**
```hcl
resource "yandex_compute_instance" "main" {
  name = var.vm_name
  resources {
    cores  = var.vm_cores
    memory = var.vm_memory
  }
}
```

**Pulumi (Python):**
```python
instance = yandex.ComputeInstance(
    "devops-vm",
    name=vm_name,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=vm_cores,
        memory=vm_memory,
    ),
)
```

## Important Notes

- ⚠️ **Never commit `Pulumi.*.yaml` files** - they may contain secrets
- ⚠️ **Never commit `venv/` directory** - it's a local Python environment
- ✅ Use free tier instance settings to avoid costs
- ✅ Run `pulumi destroy` when done
- ✅ Use `--secret` flag for sensitive configuration

## Troubleshooting

### Import Errors
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Authentication Errors
```bash
# Check Pulumi config
pulumi config

# Verify Yandex Cloud token
yc iam create-token
```

### Stack Issues
```bash
# List stacks
pulumi stack ls

# Select stack
pulumi stack select dev

# Force unlock if stuck
pulumi cancel
```
