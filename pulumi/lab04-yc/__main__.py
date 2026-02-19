import os
import pathlib

import pulumi
import pulumi_yandex as yandex



ZONE = "ru-central1-a"


FOLDER_ID = "b1g1cmmbss046n25oln3"

SSH_PUBLIC_KEY_PATH = os.path.expanduser("~/.ssh/id_ed25519.pub")

SSH_USERNAME = "ubuntu"



def read_ssh_public_key(path: str) -> str:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"SSH public key not found: {p}")
    return p.read_text().strip()


ssh_pub = read_ssh_public_key(SSH_PUBLIC_KEY_PATH)



net = yandex.VpcNetwork(
    "lab-network",
    folder_id=FOLDER_ID,
)

subnet = yandex.VpcSubnet(
    "lab-subnet",
    folder_id=FOLDER_ID,
    network_id=net.id,
    zone=ZONE,
    v4_cidr_blocks=["10.0.0.0/24"],
)



sg = yandex.VpcSecurityGroup(
    "lab-sg",
    folder_id=FOLDER_ID,
    network_id=net.id,
    description="Security group for lab04 VM (SSH, HTTP, app port)",
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outbound",
            v4_cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535,
        )
    ],
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=22,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="App port 5000",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000,
        ),
    ],
)



image = yandex.get_compute_image(
    family="ubuntu-2004-lts",
    folder_id="standard-images",
)



vm = yandex.ComputeInstance(
    "lab-vm",
    folder_id=FOLDER_ID,
    zone=ZONE,
    platform_id="standard-v2",
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
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id],
        )
    ],
    metadata={
        "ssh-keys": f"{SSH_USERNAME}:{ssh_pub}",
    },
    labels={
        "lab": "lab04",
        "tool": "pulumi",
    },
)


pulumi.export("external_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("zone", vm.zone)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", sg.id)
