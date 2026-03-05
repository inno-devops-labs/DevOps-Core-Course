import pathlib

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

aws_region = config.get("awsRegion") or "us-east-1"
availability_zone = config.get("availabilityZone") or "us-east-1a"
project_name = config.get("projectName") or "devops-core-lab04"
instance_type = config.get("instanceType") or "t2.micro"
instance_username = config.get("instanceUsername") or "ubuntu"
vpc_cidr = config.get("vpcCidr") or "10.20.0.0/16"
public_subnet_cidr = config.get("publicSubnetCidr") or "10.20.1.0/24"
ssh_allowed_cidrs = config.get_object("sshAllowedCidrs") or ["0.0.0.0/0"]
ssh_public_key_path = config.get("sshPublicKeyPath") or "~/.ssh/id_rsa.pub"
key_pair_name = config.get("keyPairName") or "devops-core-lab04-key"

public_key = pathlib.Path(ssh_public_key_path).expanduser().read_text(encoding="utf-8").strip()

vpc = aws.ec2.Vpc(
    "lab04-vpc",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": f"{project_name}-vpc", "Project": project_name, "Lab": "lab04"},
)

subnet = aws.ec2.Subnet(
    "lab04-public-subnet",
    vpc_id=vpc.id,
    cidr_block=public_subnet_cidr,
    availability_zone=availability_zone,
    map_public_ip_on_launch=True,
    tags={"Name": f"{project_name}-public-subnet", "Project": project_name, "Lab": "lab04"},
)

igw = aws.ec2.InternetGateway(
    "lab04-igw",
    vpc_id=vpc.id,
    tags={"Name": f"{project_name}-igw", "Project": project_name, "Lab": "lab04"},
)

route_table = aws.ec2.RouteTable(
    "lab04-public-rt",
    vpc_id=vpc.id,
    routes=[aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id)],
    tags={"Name": f"{project_name}-public-rt", "Project": project_name, "Lab": "lab04"},
)

aws.ec2.RouteTableAssociation(
    "lab04-public-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
)

security_group = aws.ec2.SecurityGroup(
    "lab04-sg",
    vpc_id=vpc.id,
    description="Security group for Lab 04 VM",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=ssh_allowed_cidrs,
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
    tags={"Name": f"{project_name}-sg", "Project": project_name, "Lab": "lab04"},
)

key_pair = aws.ec2.KeyPair(
    "lab04-keypair",
    key_name=key_pair_name,
    public_key=public_key,
)

ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]),
        aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
    ],
)

instance = aws.ec2.Instance(
    "lab04-vm",
    ami=ubuntu_ami.id,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    key_name=key_pair.key_name,
    associate_public_ip_address=True,
    tags={"Name": f"{project_name}-vm", "Project": project_name, "Lab": "lab04"},
)

pulumi.export("vmPublicIp", instance.public_ip)
pulumi.export("sshCommand", pulumi.Output.concat("ssh ", instance_username, "@", instance.public_ip))
pulumi.export("securityGroupId", security_group.id)
