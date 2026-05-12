import os
import pulumi
from pulumi_yandex import (
    VpcNetwork, VpcSubnet, VpcSecurityGroup,
    ComputeInstance, ComputeImage
)

cloud_id = os.environ.get("YC_CLOUD_ID")
folder_id = os.environ.get("YC_FOLDER_ID")
zone = os.environ.get("YC_ZONE", "ru-central1-a")

if not cloud_id or not folder_id:
    raise ValueError("YC_CLOUD_ID and YC_FOLDER_ID must be set")

import os
ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
with open(ssh_key_path, "r") as f:
    ssh_public_key = f.read().strip()

network = VpcNetwork(
    "pulumi-lab-network",
    name="pulumi-lab-network",
    description="Network for Pulumi Lab4 VM",
    labels={
        "environment": "lab",
        "managed-by": "pulumi",
        "course": "devops",
        "lab": "04"
    }
)

subnet = VpcSubnet(
    "pulumi-lab-subnet",
    name="pulumi-lab-subnet",
    description="Subnet for Pulumi Lab4 VM",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.20.0/24"],
    labels={
        "environment": "lab",
        "managed-by": "pulumi"
    }
)

security_group = VpcSecurityGroup(
    "pulumi-lab-sg",
    name="pulumi-lab-sg",
    description="Security group for Pulumi Lab4 VM",
    network_id=network.id,
    ingresses=[  # Changed from 'ingress' to 'ingresses'
        {
            "protocol": "TCP",
            "description": "SSH access",
            "port": 22,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "TCP",
            "description": "HTTP web traffic",
            "port": 80,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "TCP",
            "description": "Application port",
            "port": 5000,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egresses=[  # Changed from 'egress' to 'egresses'
        {
            "protocol": "ANY",
            "description": "Allow all outgoing",
            "v4_cidr_blocks": ["0.0.0.0/0"],
            "from_port": 0,
            "to_port": 65535,
        }
    ],
    labels={
        "environment": "lab",
        "managed-by": "pulumi"
    }
)

image = ComputeImage("ubuntu-image", source_family="ubuntu-2204-lts")

vm = ComputeInstance(
    "pulumi-lab-vm",
    name="pulumi-lab-vm",
    description="Pulumi Lab4 virtual machine",
    platform_id="standard-v2",
    zone=zone,
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20,
    },
    boot_disk={
        "auto_delete": True,
        "initialize_params": {
            "image_id": image.id,
            "size": 10,
            "type": "network-hdd",
        }
    },
    network_interfaces=[{
        "subnet_id": subnet.id,
        "security_group_ids": [security_group.id],
        "nat": True,
    }],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}",
    },
    allow_stopping_for_update=True,
    labels={
        "environment": "lab",
        "managed-by": "pulumi",
        "course": "devops",
        "lab": "04"
    }
)

pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("vm_id", vm.id)
pulumi.export("ssh_command", pulumi.Output.concat("ssh -i ~/.ssh/lab4-key ubuntu@", vm.network_interfaces[0].nat_ip_address))

