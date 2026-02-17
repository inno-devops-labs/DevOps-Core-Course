"""
Lab 04 - Pulumi Infrastructure as Code
Provisions a VM on Yandex Cloud with network and security configuration
"""

import pulumi
import pulumi_yandex as yandex

# Get configuration
config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
vm_name = config.get("vm_name") or "lab04-pulumi-vm"
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"
ssh_allowed_cidr = config.require("ssh_allowed_cidr")  # CIDR allowed to SSH, e.g. 203.0.113.10/32

# Read SSH public key
with open(ssh_public_key_path.replace("~", pulumi.runtime.get_config("HOME") or "~"), "r") as f:
    ssh_public_key = f.read().strip()

# Get latest Ubuntu 24.04 image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-2404-lts",
    folder_id="standard-images"
)

# Create VPC network
network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-pulumi-network",
    description="Network for Lab 04 Pulumi VM",
    folder_id=folder_id
)

# Create subnet
subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-pulumi-subnet",
    description="Subnet for Lab 04 Pulumi VM",
    v4_cidr_blocks=["10.128.0.0/24"],
    zone=zone,
    network_id=network.id,
    folder_id=folder_id
)

# Create security group
security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="lab04-pulumi-security-group",
    description="Security group for Lab 04 Pulumi VM",
    network_id=network.id,
    folder_id=folder_id,
    ingresses=[
        # Allow SSH from specific IP
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow SSH from my IP",
            v4_cidr_blocks=[ssh_allowed_cidr],
            port=22
        ),
        # Allow HTTP
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80
        ),
        # Allow custom port 5000
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow app port 5000",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000
        ),
    ],
    egresses=[
        # Allow all outbound traffic
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outbound traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535
        ),
    ]
)

# Create VM instance
vm = yandex.ComputeInstance(
    "lab04-vm",
    name=vm_name,
    hostname=vm_name,
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20  # Free tier: 20% CPU
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=10,  # 10 GB
            type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,  # Assign public IP
            security_group_ids=[security_group.id]
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}"
    },
    labels={
        "environment": "lab04",
        "managed_by": "pulumi",
        "purpose": "devops-course"
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=False
    )
)

# Export outputs
pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("ssh_command", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {ssh_user}@{ip}"
))
pulumi.export("connection_info", {
    "public_ip": vm.network_interfaces[0].nat_ip_address,
    "private_ip": vm.network_interfaces[0].ip_address,
    "ssh_user": ssh_user,
    "ssh_command": vm.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {ssh_user}@{ip}"
    )
})