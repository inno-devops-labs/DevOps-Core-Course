"""Lab04 Pulumi program (AWS EC2 + VPC)."""

from __future__ import annotations

import pathlib
import urllib.request

import pulumi
import pulumi_aws as aws


def _get_my_ip_cidr() -> str | None:
    try:
        with urllib.request.urlopen("https://checkip.amazonaws.com/", timeout=5) as resp:
            ip = resp.read().decode("utf-8").strip()
            if ip:
                return f"{ip}/32"
    except Exception:
        return None
    return None


config = pulumi.Config()
project_name = config.get("projectName") or "lab04"
instance_type = config.get("instanceType") or "t2.micro"
ssh_ingress_cidr = config.get("sshIngressCidr") or _get_my_ip_cidr()

if not ssh_ingress_cidr:
    ssh_ingress_cidr = "0.0.0.0/0"
    pulumi.log.warn("Could not detect public IP; SSH will be open to 0.0.0.0/0.")


common_tags = {
    "Project": project_name,
    "Lab": "lab04",
    "Managed": "pulumi",
}


ubuntu_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],  # Canonical
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(name="virtualization-type", values=["hvm"]),
    ],
)

azs = aws.get_availability_zones(state="available")
az0 = azs.names[0]

vpc = aws.ec2.Vpc(
    f"{project_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={**common_tags, "Name": f"{project_name}-vpc"},
)

igw = aws.ec2.InternetGateway(
    f"{project_name}-igw",
    vpc_id=vpc.id,
    tags={**common_tags, "Name": f"{project_name}-igw"},
)

subnet = aws.ec2.Subnet(
    f"{project_name}-public-subnet",
    vpc_id=vpc.id,
    availability_zone=az0,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    tags={**common_tags, "Name": f"{project_name}-public-subnet"},
)

rt = aws.ec2.RouteTable(
    f"{project_name}-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id),
    ],
    tags={**common_tags, "Name": f"{project_name}-public-rt"},
)

aws.ec2.RouteTableAssociation(
    f"{project_name}-public-rt-assoc",
    subnet_id=subnet.id,
    route_table_id=rt.id,
)

sg = aws.ec2.SecurityGroup(
    f"{project_name}-sg",
    description="Lab04 SG: SSH(22) from my IP, HTTP(80) and app(5000)",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="SSH from my IP",
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=[ssh_ingress_cidr],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTP",
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            description="App port",
            protocol="tcp",
            from_port=5000,
            to_port=5000,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="All egress",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={**common_tags, "Name": f"{project_name}-sg"},
)

pubkey_path = pathlib.Path(__file__).resolve().parent.parent / "terraform" / "keys" / "lab04_terraform_key.pub"
public_key = pubkey_path.read_text(encoding="utf-8").strip()

key_pair = aws.ec2.KeyPair(
    f"{project_name}-key",
    key_name=f"{project_name}-key",
    public_key=public_key,
    tags={**common_tags, "Name": f"{project_name}-key"},
)

instance = aws.ec2.Instance(
    f"{project_name}-vm",
    ami=ubuntu_ami.id,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    key_name=key_pair.key_name,
    tags={**common_tags, "Name": f"{project_name}-vm"},
)

eip = aws.ec2.Eip(
    f"{project_name}-eip",
    domain="vpc",
    tags={**common_tags, "Name": f"{project_name}-eip"},
)

aws.ec2.EipAssociation(
    f"{project_name}-eip-assoc",
    instance_id=instance.id,
    allocation_id=eip.id,
)

pulumi.export("public_ip", eip.public_ip)
pulumi.export("instance_id", instance.id)
pulumi.export("security_group_id", sg.id)
pulumi.export(
    "ssh_command",
    pulumi.Output.concat("ssh -i terraform/keys/lab04_terraform_key ubuntu@", eip.public_ip),
)
