import pulumi
import pulumi_aws as aws

vpc = aws.ec2.get_vpc(default=True)

subnets = aws.ec2.get_subnets(filters=[
    {"name": "vpc-id", "values": [vpc.id]}
])

sg = aws.ec2.SecurityGroup("lab-sg",
    vpc_id=vpc.id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 5000,
            "to_port": 5000,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        {
            "name": "name",
            "values": ["ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*"],
        }
    ],
)

instance = aws.ec2.Instance("lab-vm",
    instance_type="t2.micro",
    ami=ami.id,
    subnet_id=subnets.ids[0],
    vpc_security_group_ids=[sg.id],
    key_name="vockey",
)

pulumi.export("public_ip", instance.public_ip)