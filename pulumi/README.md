# Pulumi — Yandex Cloud VM (Python)

## Prerequisites

- Pulumi CLI >= 3.x
- Python >= 3.9
- Yandex Cloud account with service account key
- SSH key pair

## Setup

1. Initialize the stack:

```bash
cd pulumi/
pulumi stack init dev
```

2. Configure Yandex Cloud credentials:

```bash
export YC_SERVICE_ACCOUNT_KEY_FILE=~/yc-key.json
export YC_CLOUD_ID=your-cloud-id
export YC_FOLDER_ID=your-folder-id

pulumi config set zone ru-central1-a
pulumi config set ssh_user ubuntu
pulumi config set ssh_public_key_path ~/.ssh/id_rsa.pub
```

3. Create venv and install deps:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Deploy:

```bash
pulumi preview
pulumi up
```

## Cleanup

```bash
pulumi destroy
pulumi stack rm dev
```

## Resources Created

Same as Terraform: VPC network, subnet, security group (SSH/HTTP/5000), Ubuntu 24.04 VM.
