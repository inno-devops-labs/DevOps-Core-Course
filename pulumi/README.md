# Pulumi (lab04)

Same infrastructure as Terraform: VM on Yandex Cloud with network, subnet, security group.

## Setup

```bash
cd pulumi
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Config

```bash
pulumi config set cloud_id <your-cloud-id>
pulumi config set folder_id <your-folder-id>
pulumi config set zone ru-central1-a
pulumi config set my_ip <your-ip>/32
```

Auth: `export YC_TOKEN="$(yc iam create-token)"`

## Run

```bash
pulumi preview
pulumi up
pulumi stack output
```
