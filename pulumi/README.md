# Pulumi Lab 04 (AWS, Python)

## Prerequisites
- Pulumi CLI
- Python 3.11+
- AWS credentials configured
- Existing SSH public key

## Quick Start
```bash
cd pulumi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi config set awsRegion us-east-1
pulumi config set availabilityZone us-east-1a
pulumi config set sshAllowedCidrs '["x.x.x.x/32"]' --path
pulumi config set sshPublicKeyPath ~/.ssh/id_rsa.pub
pulumi preview
pulumi up
```

## Destroy
```bash
pulumi destroy
```

## Notes
- Keep `Pulumi.<stack>.yaml` out of git (already ignored in root `.gitignore`).
- Restrict SSH CIDR to your own IP.
