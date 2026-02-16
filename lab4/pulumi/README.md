# Lab 04 — Task 2 (Pulumi VM Creation, Yandex Cloud)

## Prerequisites

- Pulumi CLI installed
- Python 3.12+ available
- Service account authorized key JSON file

## Configure stack

```bash
cd pulumi
pulumi login --local
pulumi stack select dev

pulumi config set cloudId "<cloud-id>"
pulumi config set folderId "<folder-id>"
pulumi config set zone "ru-central1-d"
pulumi config set serviceAccountKeyFile "/absolute/path/to/authorized_key.json"
pulumi config set sshAllowedCidr "<your-ip>/32"
pulumi config set sshUser "ubuntu"
pulumi config set sshPublicKeyPath "/Users/your-user/.ssh/id_rsa.pub"
```

Optional (for folders with strict VPC network quotas):

```bash
pulumi config set existingInstanceIdForNetwork "<existing-instance-id>"
```

## Deploy

```bash
PULUMI_CONFIG_PASSPHRASE="<passphrase>" pulumi preview --non-interactive
PULUMI_CONFIG_PASSPHRASE="<passphrase>" pulumi up --yes --non-interactive
```

## SSH

```bash
PULUMI_CONFIG_PASSPHRASE="<passphrase>" pulumi stack output sshCommand
```
