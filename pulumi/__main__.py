"""Infrastructure for Lab 4 using Pulumi and Yandex Cloud"""

import pulumi
import pulumi_yandex as yandex
import os

# Configuration
config = pulumi.Config()
cloud_id = config.require("cloud_id") or os.environ.get("YC_CLOUD_ID")
folder_id = config.require("folder_id") or os.environ.get("YC_FOLDER_ID")
zone = config.get("zone") or "ru-central1-a"

# Get public SSH key
ssh_public_key_path = os.path.expanduser("~/.ssh/id_ed25519.pub")
if os.path.exists(ssh_public_key_path):
    with open(ssh_public_key_path, 'r') as f:
        ssh_public_key = f.read().strip()
else:
    ssh_public_key = config.require("ssh_public_key")

# VPC Network
network = yandex.VpcNetwork(
    "lab4-network-pulumi",
    name="lab4-pulumi-network",
    description="Network for Lab 4 Pulumi VM",
)

# Subnet - use different CIDR to avoid conflicts
subnet = yandex.VpcSubnet(
    "lab4-subnet-pulumi",
    name="lab4-pulumi-subnet",
    description="Subnet for Lab 4 Pulumi VM",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.20.0.0/24"],  # Different from Terraform's 10.10.0.0/24
)

# Security Group with ingress/egress rules
security_group = yandex.VpcSecurityGroup(
    "lab4-sg-pulumi",
    name="lab4-pulumi-sg",
    description="Security group for Lab 4 Pulumi VM",
    network_id=network.id,
)

# SSH ingress rule
ssh_rule = yandex.VpcSecurityGroupRule(
    "lab4-sg-rule-ssh",
    security_group_binding=security_group.id,
    direction="ingress",
    description="SSH",
    protocol="TCP",
    port=22,
    v4_cidr_blocks=["0.0.0.0/0"],
)

# HTTP ingress rule
http_rule = yandex.VpcSecurityGroupRule(
    "lab4-sg-rule-http",
    security_group_binding=security_group.id,
    direction="ingress",
    description="HTTP",
    protocol="TCP",
    port=80,
    v4_cidr_blocks=["0.0.0.0/0"],
)

# App port 5000 ingress rule
app_rule = yandex.VpcSecurityGroupRule(
    "lab4-sg-rule-app",
    security_group_binding=security_group.id,
    direction="ingress",
    description="App Port",
    protocol="TCP",
    port=5000,
    v4_cidr_blocks=["0.0.0.0/0"],
)

# Egress rule (allow all outbound)
egress_rule = yandex.VpcSecurityGroupRule(
    "lab4-sg-rule-egress",
    security_group_binding=security_group.id,
    direction="egress",
    description="Outbound",
    protocol="ANY",
    from_port=0,
    to_port=65535,
    v4_cidr_blocks=["0.0.0.0/0"],
)

# Get latest Ubuntu image
image = yandex.get_compute_image(
    family="ubuntu-2404-lts-oslogin",
    folder_id="standard-images",
)

# VM Instance
vm = yandex.ComputeInstance(
    "lab4-vm-pulumi",
    name="lab4-pulumi-vm",
    description="VM for Lab 4 - Pulumi implementation",
    platform_id="standard-v2",
    zone=zone,
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20,
    },
    boot_disk={
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
        "user-data": f"""#cloud-config
users:
  - name: ubuntu
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    groups: sudo
    shell: /bin/bash
    ssh-authorized-keys:
      - {ssh_public_key}
packages:
  - curl
  - wget
  - git
  - htop
  - docker.io
package_update: true
runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ubuntu
  - echo "Lab 4 VM ready for Ansible Lab 5! (Created with Pulumi)" > /etc/motd
"""
    },
    opts=pulumi.ResourceOptions(depends_on=[ssh_rule, http_rule, app_rule, egress_rule])
)

# Export outputs
pulumi.export("vm_name", vm.name)
pulumi.export("vm_id", vm.id)
pulumi.export("private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export(
    "ssh_command",
    vm.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh ubuntu@{ip}"
    ),
)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)