"""
Pulumi program for Yandex Cloud VM — Lab 4 Infrastructure as Code.
Recreates the same infrastructure as the Terraform configuration.
"""

import pulumi
import pulumi_yandex as yandex

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
yc_zone = config.get("zone") or "ru-central1-a"
vm_user = config.get("vmUser") or "ubuntu"
ssh_public_key_path = config.get("sshPublicKeyPath") or "~/.ssh/id_rsa.pub"
existing_network_id = config.get("existingNetworkId")
existing_subnet_id = config.get("existingSubnetId")

# Read SSH public key
import os

ssh_key_path = os.path.expanduser(ssh_public_key_path)
with open(ssh_key_path, "r") as f:
    ssh_public_key = f.read().strip()

# ---------------------------------------------------------------------------
# Data source — latest Ubuntu 24.04 LTS image
# ---------------------------------------------------------------------------
ubuntu_image = yandex.get_compute_image(family="ubuntu-2404-lts-oslogin")

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
resolved_network_id = existing_network_id

if existing_subnet_id and not resolved_network_id:
    existing_subnet = yandex.get_vpc_subnet(subnet_id=existing_subnet_id)
    resolved_network_id = existing_subnet.network_id

if resolved_network_id:
    network_id = resolved_network_id
else:
    network = yandex.VpcNetwork(
        "lab04-network",
        name="lab04-network",
    )
    network_id = network.id

if existing_subnet_id:
    subnet_id = existing_subnet_id
else:
    subnet = yandex.VpcSubnet(
        "lab04-subnet",
        name="lab04-subnet",
        zone=yc_zone,
        network_id=network_id,
        v4_cidr_blocks=["10.0.1.0/24"],
    )
    subnet_id = subnet.id

# ---------------------------------------------------------------------------
# Security Group — allow SSH (22), HTTP (80), App (5000)
# ---------------------------------------------------------------------------
security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="lab04-sg",
    network_id=network_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow app port",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Compute Instance (free-tier: 2 cores @ 20%, 1 GB RAM)
# ---------------------------------------------------------------------------
instance = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
    platform_id="standard-v2",
    zone=yc_zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet_id,
            nat=True,
            security_group_ids=[security_group.id],
        ),
    ],
    metadata={
        "ssh-keys": f"{vm_user}:{ssh_public_key}",
    },
    labels={
        "project": "devops-lab04",
        "tool": "pulumi",
    },
)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", instance.name)
pulumi.export(
    "ssh_connection",
    instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {vm_user}@{ip}"
    ),
)
pulumi.export("subnet_id", subnet_id)
pulumi.export("security_group_id", security_group.id)
