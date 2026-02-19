# Pulumi — Yandex Cloud VM (Python)

Recreates the same infrastructure as Terraform using Pulumi with Python.

## Prerequisites

- Pulumi CLI >= 3.x
- Python >= 3.9
- Yandex Cloud account with configured CLI

## Usage

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

pulumi stack init dev
pulumi config set yandex:token YOUR_TOKEN --secret
pulumi config set yandex:cloudId YOUR_CLOUD_ID
pulumi config set yandex:folderId YOUR_FOLDER_ID
pulumi config set sshPublicKey "ssh-rsa AAAA..."

pulumi preview
pulumi up
```

## Connect to VM

```bash
pulumi stack output ssh_command
```

## Cleanup

```bash
pulumi destroy
pulumi stack rm dev
```
