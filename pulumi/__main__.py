"""Pulumi program to create an AWS EC2 instance with networking — Lab 04."""

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
allowed_ssh_cidr = config.require("allowedSshCidr")
ssh_public_key = config.require_secret("sshPublicKey")

# ---------------------------
# Networking
# ---------------------------

vpc = aws.ec2.Vpc(
    "lab04-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "lab04-vpc"},
)

igw = aws.ec2.InternetGateway(
    "lab04-igw",
    vpc_id=vpc.id,
    tags={"Name": "lab04-igw"},
)

subnet = aws.ec2.Subnet(
    "lab04-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone="us-east-1a",
    tags={"Name": "lab04-subnet"},
)

route_table = aws.ec2.RouteTable(
    "lab04-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={"Name": "lab04-rt"},
)

aws.ec2.RouteTableAssociation(
    "lab04-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

# ---------------------------
# Security Group
# ---------------------------

sg = aws.ec2.SecurityGroup(
    "lab04-sg",
    description="Allow SSH, HTTP and app port",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=[allowed_ssh_cidr],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP",
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="App port",
            from_port=5000,
            to_port=5000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={"Name": "lab04-sg"},
)

# ---------------------------
# AMI (Ubuntu 24.04)
# ---------------------------

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"],
        ),
    ],
)

# ---------------------------
# SSH Key
# ---------------------------

key_pair = aws.ec2.KeyPair(
    "lab04-key",
    key_name="lab04-key",
    public_key=ssh_public_key,
)

# ---------------------------
# EC2 Instance
# ---------------------------

instance = aws.ec2.Instance(
    "lab04-vm",
    ami=ami.id,
    instance_type="t2.micro",
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    key_name=key_pair.key_name,
    tags={"Name": "lab04-vm"},
)

# ---------------------------
# Outputs
# ---------------------------

pulumi.export("public_ip", instance.public_ip)
pulumi.export("ssh_command", instance.public_ip.apply(lambda ip: f"ssh ubuntu@{ip}"))
