"""Lab 4 - Create VM on Yandex Cloud (same as Terraform)."""
import os
import pulumi

config = pulumi.Config()
key_file = config.get("yandex_service_account_key_file")
if key_file:
    os.environ["YANDEX_SERVICE_ACCOUNT_KEY_FILE"] = key_file

import pulumi_yandex as yandex

folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
ssh_public_key = config.require("ssh_public_key")
ssh_cidr = config.require("ssh_cidr")

# Ubuntu 22.04 LTS
image = yandex.get_compute_image(family="ubuntu-2204-lts")

network = yandex.VpcNetwork(
    "lab4c-network",
    name="lab4c-network",
    folder_id=folder_id,
)

subnet = yandex.VpcSubnet(
    "lab4c-subnet",
    name="lab4c-subnet",
    network_id=network.id,
    zone=zone,
    folder_id=folder_id,
    v4_cidr_blocks=["10.0.1.0/24"],
)

sg = yandex.VpcSecurityGroup(
    "lab4c-vm-sg",
    name="lab4c-vm-sg",
    network_id=network.id,
    folder_id=folder_id,
    description="Allow SSH, HTTP, and port 5000 for Lab 4",
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            port=22,
            protocol="TCP",
            v4_cidr_blocks=[ssh_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            port=80,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="App 5000",
            port=5000,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Any",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

vm = yandex.ComputeInstance(
    "lab4c-vm",
    name="lab4c-vm",
    zone=zone,
    folder_id=folder_id,
    platform_id="standard-v3",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id],
        ),
    ],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}",
    },
    labels={"lab": "lab04"},
)

pulumi.export("public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ubuntu@", vm.network_interfaces[0].nat_ip_address))
