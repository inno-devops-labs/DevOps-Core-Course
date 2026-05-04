import os
import pulumi
import pulumi_aws as aws

# Config
config = pulumi.Config()
region = config.get("aws:region") or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

# SSH public key (same one you generated for Terraform)
pubkey_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
with open(pubkey_path, "r", encoding="utf-8") as f:
    public_key = f.read().strip()

key_pair = aws.ec2.KeyPair(
    "lab04-key",
    key_name="lab04-key",
    public_key=public_key,
)

sg = aws.ec2.SecurityGroup(
    "lab04-sg",
    description="Lab04 SG: allow SSH and HTTP",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
            description="SSH",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="All outbound",
        )
    ],
)

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
)

user_data = """#!/bin/bash
set -eux
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "lab04 nginx ok" > /var/www/html/index.html
echo "user-data pulumi v1" > /var/tmp/user-data-version
"""

instance = aws.ec2.Instance(
    "lab04-vm",
    ami=ami.id,
    instance_type="t3.micro",
    vpc_security_group_ids=[sg.id],
    key_name=key_pair.key_name,
    user_data=user_data,
    tags={"Name": "lab04-vm"},
)

pulumi.export("public_ip", instance.public_ip)
pulumi.export("ssh_command", pulumi.Output.concat("ssh -i ~/.ssh/id_ed25519 ubuntu@", instance.public_ip))
