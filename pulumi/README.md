# Pulumi Infrastructure for Lab 4

This directory contains Pulumi configuration (Python) to provision the same infrastructure as Terraform.

## Quick Start

**Easiest:** From the repo root, run:
```bash
export YANDEX_CLOUD_ID="your-cloud-id"
export YANDEX_FOLDER_ID="your-folder-id"
./lab04_evidence.sh pulumi
```
The script uses a **local backend** (`PULUMI_BACKEND_URL=file://.`) by default, so no `pulumi login` is required. Evidence is written to `docs/lab04-evidence/`.

**Manual steps:**

1. **Install Pulumi**:
   ```bash
   brew install pulumi  # macOS
   # Or: curl -fsSL https://get.pulumi.com | sh
   ```

2. **Backend** (optional): Use local state so no login is needed:
   ```bash
   export PULUMI_BACKEND_URL=file://.
   ```
   Or run `pulumi login` for Pulumi Cloud.

3. **Setup credentials** (same as Terraform):
   ```bash
   export YANDEX_CLOUD_ID="your-cloud-id"
   export YANDEX_FOLDER_ID="your-folder-id"
   export YANDEX_SERVICE_ACCOUNT_KEY_FILE="$HOME/.yandex/key.json"
   ```

4. **Setup Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure stack**:
   ```bash
   pulumi config set project_name devops-lab4
   pulumi config set zone ru-central1-a
   MY_IP=$(curl -s ifconfig.me)
   pulumi config set ssh_allowed_cidr "${MY_IP}/32"
   pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
   ```

6. **Preview and apply**:
   ```bash
   pulumi preview
   pulumi up
   ```

7. **View outputs**:
   ```bash
   pulumi stack output
   ```

8. **Connect to VM**:
   ```bash
   ssh ubuntu@$(pulumi stack output vm_public_ip)
   ```

9. **Destroy when done**:
   ```bash
   pulumi destroy
   ```

## Files

- `__main__.py` - Main infrastructure code (Python)
- `Pulumi.yaml` - Project metadata
- `requirements.txt` - Python dependencies
- `SETUP.md` - Detailed setup instructions
- `.gitignore` - Ignores stack configs and venv

## Resources Created

Same as Terraform:
- VPC Network
- Subnet
- Security Group
- Compute Instance (Ubuntu 22.04)

## Differences from Terraform

- **Language**: Python instead of HCL
- **Approach**: Imperative (function calls) vs Declarative (HCL blocks)
- **State**: Managed by Pulumi Cloud (free tier)
- **Configuration**: `pulumi config` instead of `terraform.tfvars`

## Documentation

See `SETUP.md` for detailed setup instructions and troubleshooting.
