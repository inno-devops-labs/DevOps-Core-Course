"""
DevOps Course Lab 4 - Pulumi Infrastructure

This Pulumi program creates the same infrastructure as the Terraform configuration:
- VPC Network
- Subnet
- Security Group (with SSH, HTTP, HTTPS, and custom app ports)
- Compute Instance (VM)
- Public IP (NAT)

Cloud Provider: Yandex Cloud
"""

import pulumi
import pulumi_yandex as yandex
from typing import List

# =============================================================================
# Configuration
# =============================================================================

config = pulumi.Config()

# VM Configuration
vm_name = config.get("vm_name") or "devops-vm-pulumi"
vm_platform_id = config.get("vm_platform_id") or "standard-v2"
vm_cores = config.get_int("vm_cores") or 2
vm_core_fraction = config.get_int("vm_core_fraction") or 20
vm_memory = config.get_int("vm_memory") or 1
vm_disk_size = config.get_int("vm_disk_size") or 10
vm_disk_type = config.get("vm_disk_type") or "network-hdd"
vm_image_id = config.get("vm_image_id") or "fd8g5aftj139tv8u2mo1"  # Ubuntu 24.04 LTS
vm_user = config.get("vm_user") or "ubuntu"
vm_zone = config.get("vm_zone") or "ru-central1-a"

# Network Configuration
network_name = config.get("network_name") or "devops-network-pulumi"
subnet_name = config.get("subnet_name") or "devops-subnet-pulumi"
subnet_cidr = config.get("subnet_cidr") or "10.0.2.0/24"


def _get_cidr_list(config_key: str, default_value: List[str]) -> List[str]:
    value = config.get_object(config_key)
    if value is None:
        return default_value
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(
            f"Pulumi config '{config_key}' must be a list of CIDR strings, "
            f"for example: [\"203.0.113.5/32\"]"
        )
    return value


allowed_ssh_cidr = _get_cidr_list("allowed_ssh_cidr", [])
allowed_ingress_cidr = _get_cidr_list("allowed_ingress_cidr", ["0.0.0.0/0"])

enable_security_group = config.get_bool("enable_security_group")
if enable_security_group is None:
    enable_security_group = True
if enable_security_group:
    if not allowed_ssh_cidr:
        raise ValueError(
            "Pulumi config 'allowed_ssh_cidr' must contain your public IP/32 "
            "when enable_security_group=true."
        )
    if "0.0.0.0/0" in allowed_ssh_cidr:
        raise ValueError(
            "Pulumi config 'allowed_ssh_cidr' must not contain 0.0.0.0/0. "
            "Use your public IP in /32 format."
        )

# SSH Configuration
ssh_public_key = (config.get("ssh_public_key") or "").strip()
if not ssh_public_key:
    raise ValueError(
        "Pulumi config 'ssh_public_key' is required. "
        "Set it with: pulumi config set ssh_public_key \"$(cat ~/.ssh/id_rsa.pub)\""
    )

# Tags
environment = config.get("environment") or "lab04"
project = config.get("project") or "devops-course"

labels = {
    "environment": environment,
    "project": project,
    "managed_by": "pulumi",
}

# =============================================================================
# Network Resources
# =============================================================================

# Create VPC Network
network = yandex.VpcNetwork(
    "devops-network",
    name=network_name,
    description="VPC network for DevOps course Lab 4 (Pulumi)",
    labels=labels,
)

# Create Subnet
subnet = yandex.VpcSubnet(
    "devops-subnet",
    name=subnet_name,
    description="Subnet for DevOps VM (Pulumi)",
    zone=vm_zone,
    network_id=network.id,
    v4_cidr_blocks=[subnet_cidr],
    labels=labels,
)

# =============================================================================
# Security Group (Firewall)
# =============================================================================

security_group = None
if enable_security_group:
    security_group = yandex.VpcSecurityGroup(
        "devops-security-group",
        name="devops-security-group-pulumi",
        description="Security group for DevOps VM (Pulumi)",
        network_id=network.id,
        labels=labels,
        ingresses=[
            # Allow SSH (port 22)
            yandex.VpcSecurityGroupIngressArgs(
                description="Allow SSH access",
                protocol="TCP",
                port=22,
                v4_cidr_blocks=allowed_ssh_cidr,
            ),
            # Allow HTTP (port 80)
            yandex.VpcSecurityGroupIngressArgs(
                description="Allow HTTP access",
                protocol="TCP",
                port=80,
                v4_cidr_blocks=allowed_ingress_cidr,
            ),
            # Allow HTTPS (port 443)
            yandex.VpcSecurityGroupIngressArgs(
                description="Allow HTTPS access",
                protocol="TCP",
                port=443,
                v4_cidr_blocks=allowed_ingress_cidr,
            ),
            # Allow custom app port (port 5000)
            yandex.VpcSecurityGroupIngressArgs(
                description="Allow Flask app access",
                protocol="TCP",
                port=5000,
                v4_cidr_blocks=allowed_ingress_cidr,
            ),
            # Allow ICMP (ping)
            yandex.VpcSecurityGroupIngressArgs(
                description="Allow ICMP (ping)",
                protocol="ICMP",
                v4_cidr_blocks=allowed_ingress_cidr,
            ),
        ],
        egresses=[
            # Allow all outbound traffic
            yandex.VpcSecurityGroupEgressArgs(
                description="Allow all outbound traffic",
                protocol="ANY",
                v4_cidr_blocks=["0.0.0.0/0"],
            ),
        ],
    )

# =============================================================================
# Compute Instance (VM)
# =============================================================================

# Prepare SSH metadata
ssh_metadata = f"{vm_user}:{ssh_public_key}"

instance = yandex.ComputeInstance(
    "devops-vm",
    name=vm_name,
    platform_id=vm_platform_id,
    zone=vm_zone,
    hostname=vm_name,
    labels=labels,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=vm_cores,
        memory=vm_memory,
        core_fraction=vm_core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=vm_image_id,
            size=vm_disk_size,
            type=vm_disk_type,
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,  # Enable public IP
            security_group_ids=[security_group.id] if security_group else [],
        ),
    ],
    metadata={
        "ssh-keys": ssh_metadata,
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=True,  # Use preemptible VM for cost savings
    ),
)

# =============================================================================
# Outputs
# =============================================================================

# VM Outputs
pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", instance.network_interfaces[0].ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("vm_name", instance.name)
pulumi.export("vm_fqdn", instance.fqdn)
pulumi.export("vm_zone", instance.zone)

# Network Outputs
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export(
    "security_group_id",
    security_group.id if security_group else "Security group disabled",
)

# Connection Command
pulumi.export(
    "ssh_connection_command",
    instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {vm_user}@{ip}"
    ),
)
