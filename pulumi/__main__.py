"""
Lab 04 - Pulumi Infrastructure with Python

This Pulumi program creates the same infrastructure as the Terraform configuration:
- VPC Network
- Subnet
- VM Instance with Ubuntu 24.04

Cloud Provider: Yandex Cloud
Language: Python
"""

import pulumi
import pulumi_yandex as yandex

# Get configuration
config = pulumi.Config()
cloud_id = config.require("cloud_id")
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/yandex_cloud_key.pub"
ssh_user = config.get("ssh_user") or "ubuntu"

# Read SSH public key
with open(ssh_public_key_path.replace("~", "/Users/macbook_leonid"), "r") as f:
    ssh_public_key = f.read().strip()

# Create VPC Network
network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-network-pulumi",
    description="Network for Lab04 DevOps VM (Pulumi)",
)

# Create Subnet
subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-subnet-pulumi",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.128.0.0/24"],
    description="Subnet for Lab04 DevOps VM (Pulumi)",
)

# Get latest Ubuntu 24.04 image
ubuntu_image = yandex.get_compute_image(
    family="ubuntu-2404-lts",
    folder_id="standard-images",
)

# Cloud-init configuration
cloud_init = f"""#cloud-config
users:
  - name: {ssh_user}
    groups: sudo
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh-authorized-keys:
      - {ssh_public_key}
package_update: true
package_upgrade: true
packages:
  - curl
  - wget
  - git
  - htop
runcmd:
  - echo "Lab04 Pulumi VM initialized" > /home/{ssh_user}/welcome.txt
"""

# Create VM Instance
vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-devops-vm-pulumi",
    hostname="lab04-vm-pulumi",
    platform_id="standard-v2",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,  # 20% CPU - free tier
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=10,  # 10 GB
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,  # Assign public IP
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
        "user-data": cloud_init,
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=False,
    ),
    labels={
        "environment": "lab04",
        "course": "devops",
        "created_by": "pulumi",
        "language": "python",
    },
)

# Export outputs
pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("vm_fqdn", vm.fqdn)
pulumi.export("external_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("internal_ip", vm.network_interfaces[0].ip_address)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)

# Export SSH connection string
pulumi.export(
    "ssh_connection_string",
    pulumi.Output.concat(
        "ssh -i ~/.ssh/yandex_cloud_key ",
        ssh_user,
        "@",
        vm.network_interfaces[0].nat_ip_address,
    ),
)
