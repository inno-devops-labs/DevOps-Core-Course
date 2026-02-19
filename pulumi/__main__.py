from pathlib import Path

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
cloud_id = config.require("cloud_id")
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
my_ip = config.get("my_ip") or "0.0.0.0/0"
ssh_key_path = config.get("ssh_public_key_path") or str(Path.home() / ".ssh" / "id_rsa.pub")
ssh_user = config.get("ssh_user") or "ubuntu"

ssh_public_key = Path(ssh_key_path).expanduser().read_text().strip()

network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-network",
    folder_id=folder_id,
)

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
    folder_id=folder_id,
)

image = yandex.get_compute_image(family="ubuntu-2204-lts")

vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
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
            image_id=image.id,
            size=10,
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
        ),
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
    },
    labels={
        "environment": "lab04",
        "managed-by": "pulumi",
    },
)

public_ip = vm.network_interfaces[0].nat_ip_address
pulumi.export("vm_public_ip", public_ip)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("vm_id", vm.id)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ", ssh_user, "@", public_ip))
