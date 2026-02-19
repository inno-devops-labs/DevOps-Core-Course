"""DevOps Lab 04 - Infrastructure as Code with Pulumi (Yandex Cloud)."""

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
instance_name = config.get("instance_name") or "devops-vm"
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_public_key = config.require("ssh_public_key")

ubuntu_image = yandex.get_compute_image(family="ubuntu-2404-lts")

network = yandex.VpcNetwork(
    "devops-network",
    name="devops-network",
    folder_id=folder_id,
    labels={
        "project": "devops-course",
        "lab": "lab04",
    },
)

subnet = yandex.VpcSubnet(
    "devops-subnet",
    name="devops-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
    folder_id=folder_id,
    labels={
        "project": "devops-course",
        "lab": "lab04",
    },
)

security_group = yandex.VpcSecurityGroup(
    "devops-sg",
    name="devops-sg",
    network_id=network.id,
    folder_id=folder_id,
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
            description="Allow all outbound traffic",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    labels={
        "project": "devops-course",
        "lab": "lab04",
    },
)

instance = yandex.ComputeInstance(
    "devops-vm",
    name=instance_name,
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
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
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
    },
    labels={
        "project": "devops-course",
        "lab": "lab04",
    },
)

pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export(
    "ssh_connection",
    instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {ssh_user}@{ip}"
    ),
)
