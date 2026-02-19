# Lab 4 — Pulumi (Yandex Cloud)

Same infrastructure as the Terraform stack: one VM, VPC, subnet, security group (SSH, HTTP, 5000).

## Prerequisites

- Pulumi CLI 3.x
- Python 3.9+
- Yandex Cloud account (same auth as for Terraform: `YANDEX_TOKEN` or service account key)

## Config


```bash
pulumi config set folder_id your-yandex-folder-id
pulumi config set ssh_cidr "YOUR_IP/32"
pulumi config set ssh_public_key "$(cat %USERPROFILE%\.ssh\id_rsa.pub)"
```

```powershell
pulumi config set ssh_public_key "$(Get-Content $env:USERPROFILE\.ssh\id_rsa.pub -Raw)"
```

Optional: `pulumi config set zone ru-central1-a`

## Setup

1. Log in to Pulumi: `pulumi login`
2. Create stack: `pulumi stack init dev`
3. Install deps and run:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pulumi preview
   pulumi up
   ```

4. SSH to VM:

   ```powershell
   ssh ubuntu@$(pulumi stack output public_ip)
   ```

## Cleanup

```bash
pulumi destroy
```
