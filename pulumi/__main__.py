import pulumi
import pulumi_aws as aws

config = pulumi.Config()
project_name = config.get("projectName") or "devops-lab04"
instance_type = config.get("instanceType") or "t2.micro"
allowed_ssh_cidr = config.require("allowedSshCidr")
ssh_public_key = config.require_secret("sshPublicKey")

ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
)

vpc = aws.ec2.Vpc(
    f"{project_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{project_name}-vpc",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

igw = aws.ec2.InternetGateway(
    f"{project_name}-igw",
    vpc_id=vpc.id,
    tags={
        "Name": f"{project_name}-igw",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

subnet = aws.ec2.Subnet(
    f"{project_name}-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    map_public_ip_on_launch=False,
    tags={
        "Name": f"{project_name}-subnet",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

route_table = aws.ec2.RouteTable(
    f"{project_name}-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={
        "Name": f"{project_name}-rt",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

aws.ec2.RouteTableAssociation(
    f"{project_name}-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

security_group = aws.ec2.SecurityGroup(
    f"{project_name}-sg",
    description="Security group for Lab 04 VM",
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
        )
    ],
    tags={
        "Name": f"{project_name}-sg",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

key_pair = aws.ec2.KeyPair(
    f"{project_name}-key",
    key_name=project_name,
    public_key=ssh_public_key,
    tags={
        "Name": f"{project_name}-key",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

instance = aws.ec2.Instance(
    f"{project_name}-vm",
    ami=ubuntu_ami.id,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_type="gp3",
        volume_size=20,
        delete_on_termination=True,
    ),
    tags={
        "Name": f"{project_name}-vm",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

eip = aws.ec2.Eip(
    f"{project_name}-eip",
    instance=instance.id,
    domain="vpc",
    tags={
        "Name": f"{project_name}-eip",
        "Project": project_name,
        "Environment": "lab",
        "ManagedBy": "pulumi",
    },
)

pulumi.export("public_ip", eip.public_ip)
pulumi.export("instance_id", instance.id)
pulumi.export("ssh_command", eip.public_ip.apply(
    lambda ip: f"ssh -i ~/.ssh/devops-lab04 ubuntu@{ip}"
))
