# Pulumi — Lab 4 IaC

Same infrastructure as Terraform: one EC2 VM on AWS (free tier) with SSH, HTTP, and port 5000.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/install/)
- Python 3.9+
- AWS credentials (env or `~/.aws/credentials`)
- SSH public key at `~/.ssh/id_rsa.pub` (or set `ssh_public_key_path` in config)

## Setup

```bash
cd pulumi
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Config (optional)

```bash
pulumi config set aws:region us-east-1
pulumi config set project_name devops-lab04
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
pulumi config set allowed_ssh_cidr "YOUR_IP/32"
```

## Deploy

```bash
pulumi preview
pulumi up
pulumi stack output
```

## Cleanup

```bash
pulumi destroy
```

## Note

Destroy Terraform resources before running Pulumi (or use a different project_name/region) to avoid name conflicts (e.g. key pair name).
