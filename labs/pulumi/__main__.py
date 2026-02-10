import pulumi
import pulumi_yandex as yandex
import os

config = pulumi.Config("yandex")
zone = config.get("zone") or "ru-central1-a"

network = yandex.VpcNetwork("network-1",
    name="network-1"
)

subnet = yandex.VpcSubnet("subnet-1",
    name="subnet1",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.10.0/24"]
)

ssh_key_path = os.path.expanduser("~/.ssh/yandex_cloud.pub")
with open(ssh_key_path, "r") as f:
    ssh_key = f.read()

vm = yandex.ComputeInstance("terraform-vm",
    name="terraform-vm",
    platform_id="standard-v2",
    zone=zone,

    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2,
        core_fraction=20
    ),

    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat=True
    )],

    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd80bm0rh4rkepi5ksdi",
            size=10
        )
    ),

    metadata={
        "ssh-keys": f"ubuntu:{ssh_key}"
    }
)

external_ip = vm.network_interfaces.apply(lambda interfaces: interfaces[0].nat_ip_address)

pulumi.export("external_ip_address_vm_1", external_ip)