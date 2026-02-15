import sys
print(f"DEBUG: Using Python: {sys.executable}")
# print(f"DEBUG: Sys Path: {sys.path}")

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
image_id = config.get("image_id") or "fd8p685sjqdraf7mpkuc"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_ed25519.pub"

import os
ssh_key_path = os.path.expanduser(ssh_public_key_path)
with open(ssh_key_path, "r") as f:
    ssh_public_key = f.read().strip()

# Network
network = yandex.VpcNetwork("lab-network")

# Subnet
subnet = yandex.VpcSubnet("lab-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"])

# Security group
security_group = yandex.VpcSecurityGroup("lab-security-group",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow SSH",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow app port 5000",
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound",
        ),
    ])

# VM (free tier: 2 vCPU 20%, 1GB RAM, 10GB HDD)
instance = yandex.ComputeInstance("lab-vm",
    platform_id="standard-v2",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat=True,
        security_group_ids=[security_group.id],
    )],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}",
    },
    labels={
        "project": "devops-lab04",
        "task": "pulumi",
    })

pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("ssh_connection",
    instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh -i ~/.ssh/id_ed25519 ubuntu@{ip}"))
