import pulumi
import pulumi_aws as aws
import os

# Create a new security group that allows SSH and HTTP access
sg = aws.ec2.SecurityGroup('web-secgrp',
    description='Enable SSH and HTTP access',
    ingress=[
        { 'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 5000, 'to_port': 5000, 'cidr_blocks': ['0.0.0.0/0'] },
    ],
    egress=[
        { 'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0'] },
    ])

# Get the latest Ubuntu AMI
ami = aws.ec2.get_ami(most_recent=True,
                  owners=['099720109477'], # Canonical
                  filters=[{'name': 'name', 'values': ['ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*']}])

# Create a new key pair
with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as f:
    public_key = f.read()
key_pair = aws.ec2.KeyPair('deployer-key', public_key=public_key)

# Create a new EC2 instance
instance = aws.ec2.Instance('web-instance',
    instance_type='t2.micro',
    vpc_security_group_ids=[sg.id],
    ami=ami.id,
    key_name=key_pair.key_name,
    tags={
        'Name': 'DevOps-Lab4-VM-Pulumi',
    })

# Export the public IP of the instance
pulumi.export('public_ip', instance.public_ip)
