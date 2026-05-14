"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws

# Security Group
sg = aws.ec2.SecurityGroup(
    "devops-lab4-sg",
    description="Allow SSH, HTTP, HTTPS",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ]
)

# EC2 Instance
instance = aws.ec2.Instance(
    "DevOpsLab4",
    ami="ami-0b6c6ebed2801a5cb",  
    instance_type="t2.micro",    
    key_name="vockey",
    vpc_security_group_ids=[sg.id],
    tags={"Name": "DevOpsLab4"},
    root_block_device={"volume_size": 16}
)

# Export public IP
pulumi.export("public_ip", instance.public_ip)
pulumi.export("public_dns", instance.public_dns)
