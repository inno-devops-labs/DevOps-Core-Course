import pulumi
import pulumi_aws as aws

config = pulumi.Config("k2")

access_key = config.require_secret("accessKey")
secret_key = config.require_secret("secretKey")
region = config.require("region")
endpoint = config.require("endpoint")

# Provider для K2
k2 = aws.Provider(
    "k2",
    access_key=access_key,
    secret_key=secret_key,
    region=region,

    skip_credentials_validation=True,
    skip_metadata_api_check=True,
    skip_requesting_account_id=True,

    endpoints=[
        aws.ProviderEndpointArgs(
            ec2=endpoint
        )
    ]
)

# -------------------------
# Network (VPC)
# -------------------------

vpc = aws.ec2.Vpc(
    "lab-vpc",
    cidr_block="10.0.0.0/16",
    opts=pulumi.ResourceOptions(provider=k2)
)

subnet = aws.ec2.Subnet(
    "lab-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    opts=pulumi.ResourceOptions(provider=k2)
)

# -------------------------
# Internet Gateway
# -------------------------

igw = aws.ec2.InternetGateway(
    "lab-igw",
    vpc_id=vpc.id,
    opts=pulumi.ResourceOptions(provider=k2)
)

route_table = aws.ec2.RouteTable(
    "lab-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id
        )
    ],
    opts=pulumi.ResourceOptions(provider=k2)
)

aws.ec2.RouteTableAssociation(
    "lab-rta",
    subnet_id=subnet.id,
    route_table_id=route_table.id,
    opts=pulumi.ResourceOptions(provider=k2)
)

# -------------------------
# Security Group
# -------------------------

sg = aws.ec2.SecurityGroup(
    "lab-sg",
    vpc_id=vpc.id,
    description="Allow SSH",

    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],

    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],

    opts=pulumi.ResourceOptions(provider=k2)
)

# -------------------------
# VM
# -------------------------

instance = aws.ec2.Instance(
    "lab-instance",
    instance_type="standard-2",  # поставь ТУ ЖЕ что в Terraform
    ami="ami-xxxxxxxx",          # ТУ ЖЕ что в Terraform
    subnet_id=subnet.id,
    vpc_security_group_ids=[sg.id],
    associate_public_ip_address=True,
    key_name="your-key-name",    # тот же SSH key
    opts=pulumi.ResourceOptions(provider=k2)
)

pulumi.export("public_ip", instance.public_ip)
