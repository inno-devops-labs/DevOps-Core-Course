# Lab 4 — Terraform (Yandex Cloud)

Creates one VM (free tier: 2 cores 20%, 1 GB RAM, 10 GB disk), VPC, subnet, security group (SSH, HTTP, 5000), and outputs public IP.

## Prerequisites

- Terraform 1.9+
- Yandex Cloud account
- SSH key pair on your machine (e.g. `ssh-keygen`); you will use the **public** key path in Terraform

## Authentication

Use one of these (do not commit secrets):

1. **OAuth token (quick):**  
   `set YANDEX_TOKEN=your_oauth_token` (cmd) or `$env:YANDEX_TOKEN = "..."` (PowerShell)

2. **Service account key file:**  
   Create a service account in Yandex Cloud Console, create an authorized key (JSON), then:  
   `set YANDEX_SERVICE_ACCOUNT_KEY_FILE=C:\path\to\key.json`  
   or in `terraform.tfvars`: `yandex_token` (prefer env vars).

3. **Folder ID:**  
   In Console: Cloud → folder → copy ID. Set in `terraform.tfvars` as `yandex_folder_id`.

## Setup

1. Copy and edit variables:
   - **Windows:** `copy terraform.tfvars.example terraform.tfvars`
   - **Linux/macOS:** `cp terraform.tfvars.example terraform.tfvars`
   Edit:
   - `yandex_folder_id` — your folder ID
   - `yandex_zone` — e.g. `ru-central1-a`
   - `ssh_public_key_path` — full path to your `.pub` file (e.g. `C:\Users\You\.ssh\id_rsa.pub` or `%USERPROFILE%\.ssh\id_rsa.pub`)
   - `ssh_cidr` — your IP/32 (e.g. from https://ifconfig.me)

2. Initialize and apply:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. SSH to VM (no `-i` needed if you use the same key as the one in metadata):
   - **PowerShell:** `ssh ubuntu@$(terraform output -raw public_ip)`
   - Or: `ssh -i C:\path\to\your_private_key ubuntu@<public_ip>`

## Cleanup

```bash
terraform destroy
```

## Files

- `main.tf` — provider, network, subnet, security group, instance
- `variables.tf` — folder_id, zone, ssh_public_key_path, ssh_cidr
- `outputs.tf` — public_ip, ssh_command
- `terraform.tfvars` — your values (gitignored)
