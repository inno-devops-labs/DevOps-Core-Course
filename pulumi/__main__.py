"""Pulumi Infrastructure for Lab 4 - AWS EC2 Instance"""

import pulumi
import pulumi_aws as aws

# Get configuration
config = pulumi.Config()
region = config.get("aws:region") or "us-east-1"
prefix = config.get("prefix") or "lab04-pulumi"
my_ip = config.get("my_ip_address") or "0.0.0.0/0"
key_name = config.get("key_name") or "vockey"

# Get latest Ubuntu AMI
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical
    filters=[
        {"name": "name", "values": ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]},
        {"name": "virtualization-type", "values": ["hvm"]},
    ],
)

# Get existing key pair
key_pair = aws.ec2.get_key_pair(key_name=key_name)

# Create VPC
vpc = aws.ec2.Vpc(f"{prefix}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{prefix}-vpc",
        "Course": "DevOps-Core-Course",
        "Lab": "Lab04",
        "ManagedBy": "Pulumi",
        "Owner": "ellilin",
        "Purpose": "DevOps Learning",
    }
)

# Create Internet Gateway
igw = aws.ec2.InternetGateway(f"{prefix}-igw",
    vpc_id=vpc.id,
    tags={"Name": f"{prefix}-igw"}
)

# Create Subnet
subnet = aws.ec2.Subnet(f"{prefix}-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    availability_zone=f"{region}a",
    tags={"Name": f"{prefix}-subnet"}
)

# Create Route Table
route_table = aws.ec2.RouteTable(f"{prefix}-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id,
    }],
    tags={"Name": f"{prefix}-rt"}
)

# Associate Route Table with Subnet
rt_association = aws.ec2.RouteTableAssociation(f"{prefix}-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id
)

# Create Security Group
security_group = aws.ec2.SecurityGroup(f"{prefix}-sg",
    description="Allow SSH, HTTP and custom port 5000",
    vpc_id=vpc.id,
    ingress=[
        {
            "description": "SSH from my IP",
            "from_port": 22,
            "to_port": 22,
            "protocol": "tcp",
            "cidr_blocks": [my_ip],
        },
        {
            "description": "HTTP from anywhere",
            "from_port": 80,
            "to_port": 80,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "description": "App port 5000",
            "from_port": 5000,
            "to_port": 5000,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[{
        "description": "Allow all outbound traffic",
        "from_port": 0,
        "to_port": 0,
        "protocol": "-1",
        "cidr_blocks": ["0.0.0.0/0"],
    }],
    tags={
        "Name": f"{prefix}-sg",
        "Course": "DevOps-Core-Course",
        "Lab": "Lab04",
        "ManagedBy": "Pulumi",
        "Owner": "ellilin",
    }
)

# Create EC2 Instance
instance = aws.ec2.Instance(f"{prefix}-instance",
    ami=ami.id,
    instance_type="t2.micro",
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    associate_public_ip_address=True,
    metadata_options={
        "http_endpoint": "enabled",
        "http_tokens": "required",
        "http_put_response_hop_limit": 1,
    },
    tags={
        "Name": f"{prefix}-instance",
        "Course": "DevOps-Core-Course",
        "Lab": "Lab04",
        "ManagedBy": "Pulumi",
        "Owner": "ellilin",
        "Purpose": "DevOps Learning",
    }
)

# Export outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("instance_id", instance.id)
pulumi.export("instance_public_ip", instance.public_ip)
pulumi.export("instance_public_dns", instance.public_dns)
pulumi.export("ssh_connection_string", f"ssh -i ~/.ssh/keys/labsuser.pem ubuntu@{instance.public_ip}")
