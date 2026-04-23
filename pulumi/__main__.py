"""
Pulumi — Yandex Cloud VM (Lab 04)

Recreates the same infrastructure as the Terraform configuration:
  • VPC network + subnet
  • Security group (SSH 22, HTTP 80, App 5000, ICMP)
  • Compute instance (Ubuntu 24.04 LTS, free‑tier)
"""

import os

import pulumi
import pulumi_yandex as yandex

# ---------------------------------------------------------------------------
# Configuration (set via `pulumi config set <key> <value>`)
# ---------------------------------------------------------------------------
config = pulumi.Config()

yc_zone = config.get("zone") or "ru-central1-a"
vm_name = config.get("vmName") or "devops-vm"
vm_user = config.get("vmUser") or "ubuntu"
ssh_public_key_path = config.get("sshPublicKeyPath") or "~/.ssh/id_ed25519.pub"

# Read the SSH public key from disk
ssh_pub_key_file = os.path.expanduser(ssh_public_key_path)
with open(ssh_pub_key_file, "r") as f:
    ssh_public_key = f.read().strip()

# ---------------------------------------------------------------------------
# Data source — latest Ubuntu 24.04 image
# ---------------------------------------------------------------------------
ubuntu_image = yandex.get_compute_image(family="ubuntu-2404-lts")

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
network = yandex.VpcNetwork(
    "devops-network",
    name="devops-network",
)

subnet = yandex.VpcSubnet(
    "devops-subnet",
    name="devops-subnet",
    zone=yc_zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
)

# ---------------------------------------------------------------------------
# Security Group
# ---------------------------------------------------------------------------
security_group = yandex.VpcSecurityGroup(
    "devops-sg",
    name="devops-sg",
    network_id=network.id,
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
            description="Allow app port 5000",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Allow ICMP (ping)",
            protocol="ICMP",
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
# Compute Instance (free‑tier equivalent)
# ---------------------------------------------------------------------------
instance = yandex.ComputeInstance(
    "devops-vm",
    name=vm_name,
    platform_id="standard-v2",
    zone=yc_zone,
    labels={
        "project": "devops-course",
        "lab": "lab04",
    },
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        core_fraction=20,
        memory=1,
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
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        ),
    ],
    metadata={
        "ssh-keys": f"{vm_user}:{ssh_public_key}",
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=True,
    ),
)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", instance.network_interfaces[0].ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("vm_name", instance.name)
pulumi.export(
    "ssh_command",
    instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {vm_user}@{ip}"
    ),
)
