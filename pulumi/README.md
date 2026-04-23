# Pulumi — Yandex Cloud VM

This directory contains Pulumi (Python) code that provisions the **same** infrastructure as the Terraform configuration in `../terraform/`.

## Prerequisites

| Tool | Version |
|------|---------|
| Pulumi CLI | ≥ 3.x |
| Python | ≥ 3.11 |
| Yandex Cloud account | — |
| SSH key pair | `~/.ssh/id_rsa{,.pub}` |

## Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv && source venv/bin/activate

# 2. Install Python deps
pip install -r requirements.txt

# 3. Initialise a new stack (first time only)
pulumi stack init dev

# 4. Configure Yandex Cloud credentials
pulumi config set yandex:token   YOUR_TOKEN --secret
pulumi config set yandex:cloudId YOUR_CLOUD_ID
pulumi config set yandex:folderId YOUR_FOLDER_ID

# 5. (Optional) override defaults
pulumi config set zone       ru-central1-a
pulumi config set vmName     devops-vm
pulumi config set vmUser     ubuntu

# 6. Preview & deploy
pulumi preview
pulumi up
```

## Clean Up

```bash
pulumi destroy
pulumi stack rm dev
```

## Resources Created

Identical to the Terraform version:

- `yandex.VpcNetwork` — virtual network
- `yandex.VpcSubnet` — subnet (10.0.1.0/24)
- `yandex.VpcSecurityGroup` — firewall (SSH 22, HTTP 80, App 5000)
- `yandex.ComputeInstance` — Ubuntu 24.04 LTS VM (2 vCPU @ 20 %, 1 GB RAM, 10 GB HDD)
