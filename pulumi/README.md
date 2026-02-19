# Pulumi — Yandex Cloud VM

Infrastructure as Code for Lab 4 using Pulumi (Python) with Yandex Cloud.

## Resources Created

| Resource | Type | Description |
|----------|------|-------------|
| `lab04-network` | VPC Network | Virtual private cloud |
| `lab04-subnet` | VPC Subnet | Subnet (10.0.1.0/24) |
| `lab04-sg` | Security Group | Firewall rules (SSH, HTTP, 5000) |
| `lab04-vm` | Compute Instance | Ubuntu 24.04 LTS, 2 cores @ 20%, 1 GB RAM |

## Quick Start

```bash
# 1. Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

# 2. Configure Yandex Cloud credentials
pulumi config set yandex:token YOUR_TOKEN --secret
pulumi config set yandex:cloudId YOUR_CLOUD_ID
pulumi config set yandex:folderId YOUR_FOLDER_ID

# Optional: reuse existing network/subnet if VPC quota is exceeded
pulumi config set existingSubnetId YOUR_EXISTING_SUBNET_ID
# Optional (usually not needed if existingSubnetId is set):
# pulumi config set existingNetworkId YOUR_EXISTING_NETWORK_ID

# 3. Preview
pulumi preview

# 4. Deploy
pulumi up

# 5. Connect
ssh ubuntu@$(pulumi stack output vm_public_ip)

# 6. Destroy when done
pulumi destroy
```

## Requirements

- Python >= 3.9
- Pulumi CLI >= 3.0
- Yandex Cloud account
- SSH key pair (`~/.ssh/id_rsa` / `~/.ssh/id_rsa.pub`)
