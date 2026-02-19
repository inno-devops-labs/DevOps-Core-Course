import pulumi_yandex as yandex

import pulumi

config = pulumi.Config()

# Required configuration
cloud_id = config.require("cloudId")
folder_id = config.require("folderId")

zone = config.get("zone") or "ru-central1-a"
vm_name = config.get("vmName") or "devops-vm-pulumi"
vm_cores = config.get_int("vmCores") or 2
vm_core_fraction = config.get_int("vmCoreFraction") or 20
vm_memory = config.get_int("vmMemory") or 1
vm_disk_size = config.get_int("vmDiskSize") or 10
vm_disk_type = config.get("vmDiskType") or "network-hdd"
vm_platform_id = config.get("vmPlatformId") or "standard-v2"
image_family = config.get("imageFamily") or "ubuntu-2204-lts"
ssh_user = config.get("sshUser") or "ubuntu"
ssh_public_key = config.require("sshPublicKey")
network_name = config.get("networkName") or "devops-network-pulumi"
subnet_name = config.get("subnetName") or "devops-subnet-pulumi"
sg_name = config.get("securityGroupName") or "devops-security-group-pulumi"

labels = {
    "project": "devops-course",
    "lab": "lab04",
    "managed-by": "pulumi",
}

network = yandex.VpcNetwork(
    "network",
    name=network_name,
    description="VPC network for DevOps Lab 04 (Pulumi)",
    folder_id=folder_id,
    labels=labels,
)

subnet = yandex.VpcSubnet(
    "subnet",
    name=subnet_name,
    description="Subnet for DevOps Lab 04 VM (Pulumi)",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
    folder_id=folder_id,
    labels=labels,
)

# Create Security Group
security_group = yandex.VpcSecurityGroup(
    "security-group",
    name=sg_name,
    description="Security group for DevOps Lab 04 VM - allows SSH, HTTP, and port 5000",
    network_id=network.id,
    folder_id=folder_id,
    labels=labels,
    ingresses=[
        {
            "description": "SSH access",
            "protocol": "TCP",
            "port": 22,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "description": "HTTP access",
            "protocol": "TCP",
            "port": 80,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "description": "Application port (5000)",
            "protocol": "TCP",
            "port": 5000,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egresses=[
        {
            "description": "Allow all outbound traffic",
            "protocol": "ANY",
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
    ],
)

ubuntu_image = yandex.get_compute_image(family=image_family)

vm = yandex.ComputeInstance(
    "vm",
    name=vm_name,
    description="DevOps Lab 04 VM - created with Pulumi",
    platform_id=vm_platform_id,
    zone=zone,
    folder_id=folder_id,
    labels=labels,
    resources={
        "cores": vm_cores,
        "core_fraction": vm_core_fraction,
        "memory": vm_memory,
    },
    boot_disk={
        "initialize_params": {
            "image_id": ubuntu_image.id,
            "size": vm_disk_size,
            "type": vm_disk_type,
        },
    },
    network_interfaces=[
        {
            "subnet_id": subnet.id,
            "security_group_ids": [security_group.id],
            "nat": True,
        },
    ],
    metadata={
        "ssh-keys": pulumi.Output.concat(ssh_user, ":", ssh_public_key),
    },
    scheduling_policy={
        "preemptible": False,
    },
)

pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("public_ip", vm.network_interfaces[0]["nat_ip_address"])
pulumi.export("internal_ip", vm.network_interfaces[0]["ip_address"])
pulumi.export(
    "ssh_connection_command",
    pulumi.Output.concat(
        "ssh ", ssh_user, "@", vm.network_interfaces[0]["nat_ip_address"]
    ),
)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("zone", zone)
