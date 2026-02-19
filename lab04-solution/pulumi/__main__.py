"""AWS Lab 04 Solution using Pulumi (Python)

This Pulumi program creates the same infrastructure as the Terraform solution,
but using Python and Pulumi's imperative paradigm.

Resources created:
- VPC with CIDR 10.0.0.0/16
- Public subnet with CIDR 10.0.1.0/24
- Internet Gateway
- Route Table with route to internet
- Security Group (SSH, HTTP, HTTPS)
- EC2 Instance (t2.micro - free tier)
- Elastic IP for stable public address
"""

import pulumi
import pulumi_aws as aws
import json

# Read configuration
config = pulumi.Config()

# Get configuration values with defaults
aws_region = config.get("aws_region") or "us-east-1"
environment = config.get("environment") or "lab04"
instance_type = config.get("instance_type") or "t2.micro"
vpc_cidr = config.get("vpc_cidr") or "10.0.0.0/16"
subnet_cidr = config.get("subnet_cidr") or "10.0.1.0/24"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"
ssh_allowed_cidr = config.get("ssh_allowed_cidr") or "0.0.0.0/0"

# Get SSH public key from file
import os
expanded_key_path = os.path.expanduser(ssh_public_key_path)
with open(expanded_key_path, "r") as f:
    ssh_public_key = f.read().strip()

# User data script for instance initialization
user_data_script = """#!/bin/bash
set -ex

# Update system
apt-get update
apt-get upgrade -y

# Install basic tools
apt-get install -y \\
  curl \\
  wget \\
  git \\
  vim \\
  htop \\
  net-tools

# Install Docker
apt-get install -y \\
  apt-transport-https \\
  ca-certificates \\
  curl \\
  gnupg \\
  lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Python and Ansible
apt-get install -y python3 python3-pip ansible

echo "✅ Instance setup complete"
"""

# Get the most recent Ubuntu 24.04 LTS AMI
ami_filter = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
    most_recent=True,
    owners=["099720109477"],  # Canonical
)

# Create VPC
vpc = aws.ec2.Vpc(
    f"{environment}-vpc",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{environment}-vpc",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create public subnet
subnet = aws.ec2.Subnet(
    f"{environment}-subnet",
    vpc_id=vpc.id,
    cidr_block=subnet_cidr,
    availability_zone=f"{aws_region}a",
    map_public_ip_on_launch=True,
    tags={
        "Name": f"{environment}-public-subnet",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway(
    f"{environment}-igw",
    vpc_id=vpc.id,
    tags={
        "Name": f"{environment}-igw",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create route table
route_table = aws.ec2.RouteTable(
    f"{environment}-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={
        "Name": f"{environment}-rt",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Associate route table with subnet
route_table_assoc = aws.ec2.RouteTableAssociation(
    f"{environment}-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

# Create security group
security_group = aws.ec2.SecurityGroup(
    f"{environment}-sg",
    vpc_id=vpc.id,
    description="Security group for Lab04 VMs",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=[ssh_allowed_cidr],
            description="SSH access",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP access",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTPS access",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="All outbound traffic",
        ),
    ],
    tags={
        "Name": f"{environment}-sg",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create SSH key pair
key_pair = aws.ec2.KeyPair(
    f"{environment}-key",
    public_key=ssh_public_key,
    tags={
        "Name": f"{environment}-key",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create EC2 instance
instance = aws.ec2.Instance(
    f"{environment}-vm",
    ami=ami_filter.id,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    associate_public_ip_address=True,
    user_data=user_data_script,
    tags={
        "Name": f"{environment}-vm",
        "Environment": environment,
        "Lab": "Lab04",
    },
)

# Create Elastic IP for stable public IP
eip = aws.ec2.Eip(
    f"{environment}-eip",
    instance=instance.id,
    domain="vpc",
    tags={
        "Name": f"{environment}-eip",
        "Environment": environment,
        "Lab": "Lab04",
    },
    opts=pulumi.ResourceOptions(depends_on=[igw]),
)

# Export outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("instance_id", instance.id)
pulumi.export("instance_private_ip", instance.private_ip)
pulumi.export("instance_public_ip", eip.public_ip)
pulumi.export("elastic_ip_id", eip.id)
pulumi.export(
    "ssh_connection_command",
    pulumi.concat("ssh -i ~/.ssh/id_rsa ubuntu@", eip.public_ip),
)
pulumi.export(
    "instance_details",
    {
        "instance_id": instance.id,
        "instance_type": instance.instance_type,
        "availability_zone": instance.availability_zone,
        "public_ip": eip.public_ip,
        "private_ip": instance.private_ip,
        "ami_id": instance.ami,
        "security_groups": instance.security_groups,
    },
)
