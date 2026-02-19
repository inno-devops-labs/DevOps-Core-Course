import pulumi
import pulumi_yandex as yandex

network = yandex.vpc.Network("dev-network")

subnet = yandex.vpc.Subnet(
    "dev-subnet",
    network_id=network.id,
    v4_cidr_block="10.0.0.0/24",
    zone="ru-central1-a"
)

ip = yandex.compute.IpAddress("dev-ip", region="ru-central1")

vm = yandex.compute.Instance(
    "dev-vm",
    platform_id="standard-v1",
    resources=yandex.compute.InstanceResourcesArgs(
        memory=2,
        cores=2
    ),
    boot_disk=yandex.compute.InstanceBootDiskArgs(
        initialize_params=yandex.compute.InstanceBootDiskInitializeParamsArgs(
            image_id="fd8k7u6r1q0m0k6k1vn7",
        ),
    ),
    network_interfaces=[yandex.compute.InstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat= True,
        ip_address_ids=[ip.id]
    )],
)

pulumi.export("vm_public_ip", ip.address)
