"""Lab 4 - Create VM on AWS with Pulumi (same as Terraform)."""
import os
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
project_name = config.get("project_name") or "devops-lab04"
instance_type = config.get("instance_type") or "t2.micro"
allowed_ssh_cidr = config.get("allowed_ssh_cidr") or "0.0.0.0/0"
ssh_public_key_path = config.get("ssh_public_key_path") or os.path.expanduser("~/.ssh/id_rsa.pub")

with open(ssh_public_key_path) as f:
    public_key_content = f.read()

# Latest Ubuntu 22.04 LTS AMI
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]),
        aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
    ],
)

# SSH key pair
key_pair = aws.ec2.KeyPair(
    "vm-key",
    key_name=f"{project_name}-key",
    public_key=public_key_content,
)

# Security group: SSH (22), HTTP (80), app (5000)
sg = aws.ec2.SecurityGroup(
    "vm-sg",
    name=f"{project_name}-sg",
    description="Allow SSH, HTTP, and app port 5000",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=22, to_port=22, cidr_blocks=[allowed_ssh_cidr], description="SSH"),
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"], description="HTTP"),
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=5000, to_port=5000, cidr_blocks=["0.0.0.0/0"], description="App"),
    ],
    egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
    tags={"Name": f"{project_name}-sg"},
)

# EC2 instance (free tier: t2.micro)
instance = aws.ec2.Instance(
    "vm",
    ami=ami.id,
    instance_type=instance_type,
    key_name=key_pair.key_name,
    vpc_security_group_ids=[sg.id],
    associate_public_ip_address=True,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(volume_size=8, volume_type="gp2"),
    user_data="""#!/bin/bash
apt-get update -y
apt-get install -y python3
""",
    tags={"Name": f"{project_name}-vm"},
)

pulumi.export("public_ip", instance.public_ip)
pulumi.export("instance_id", instance.id)
pulumi.export("ssh_command", instance.public_ip.apply(lambda ip: f"ssh ubuntu@{ip}"))
