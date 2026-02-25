"""Pulumi program for Lab 04 - Infrastructure as Code
Creates the same infrastructure as Terraform:
- VPC Network
- Subnet
- Security Group
- Compute Instance (VM)
"""

import pulumi
import pulumi_yandex as yandex

# Get configuration
config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
ssh_user = config.get("ssh_user") or "vglon"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/test_vm.pub"
my_ip_cidr = config.require("my_ip_cidr")

# Read SSH public key
import os
with open(os.path.expanduser(ssh_public_key_path), 'r') as f:
    ssh_public_key = f.read().strip()

# Create VPC Network
network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-network-pulumi",
    description="Network for Lab 04 DevOps VM (Pulumi)",
    folder_id=folder_id
)

# Create Subnet
subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-subnet-pulumi",
    description="Subnet for Lab 04 DevOps VM (Pulumi)",
    v4_cidr_blocks=["10.129.0.0/24"],
    zone=zone,
    network_id=network.id,
    folder_id=folder_id
)

# Create Security Group
security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="lab04-security-group-pulumi",
    description="Security group for Lab 04 VM (Pulumi)",
    network_id=network.id,
    folder_id=folder_id,
    ingresses=[
        {
            "protocol": "TCP",
            "description": "SSH access from my IP",
            "v4_cidr_blocks": [my_ip_cidr],
            "port": 22
        },
        {
            "protocol": "TCP",
            "description": "HTTP access",
            "v4_cidr_blocks": ["0.0.0.0/0"],
            "port": 80
        },
        {
            "protocol": "TCP",
            "description": "Custom app port for future deployment",
            "v4_cidr_blocks": ["0.0.0.0/0"],
            "port": 5000
        }
    ],
    egresses=[
        {
            "protocol": "ANY",
            "description": "Allow all outbound traffic",
            "v4_cidr_blocks": ["0.0.0.0/0"]
        }
    ]
)

# Get latest Ubuntu image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-2404-lts",
    folder_id="standard-images"
)

# Create Compute Instance (VM)
vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-devops-vm-pulumi",
    description="VM for Lab 04 - Infrastructure as Code (Pulumi)",
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20
    },
    boot_disk={
        "initialize_params": {
            "image_id": ubuntu_image.id,
            "size": 10,
            "type": "network-hdd"
        }
    },
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [security_group.id]
    }],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    labels={
        "lab": "lab04",
        "course": "devops",
        "tool": "pulumi",
        "purpose": "learning-iac"
    }
)

# Export outputs
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_id", vm.id)
pulumi.export("ssh_connection_command", 
              vm.network_interfaces[0].nat_ip_address.apply(
                  lambda ip: f"ssh -i ~/.ssh/test_vm {ssh_user}@{ip}"
              ))
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
