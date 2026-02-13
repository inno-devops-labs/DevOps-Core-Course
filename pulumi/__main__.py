import pulumi
import pulumi_yandex as yandex
from pulumi import Config

config = Config()
import time
zone = config.get("zone") or "ru-central1-a"
folder_id = config.require("folder_id")
my_ip = config.require("my_ip")
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_pub_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"
unique_suffix = str(int(time.time()))

# Network
network = yandex.VpcNetwork(f"lab-network-{unique_suffix}", name=f"lab-vpc-{unique_suffix}", folder_id=folder_id)

subnet = yandex.VpcSubnet(
    f"lab-subnet-{unique_suffix}",
    name=f"lab-subnet-{unique_suffix}",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.10.0.0/24"],
    folder_id=folder_id,
)

# Security group
sg = yandex.VpcSecurityGroup(
    "lab-sg",
    name="lab-sg",
    network_id=network.id,
    folder_id=folder_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(description="ssh", protocol="TCP", port=22, v4_cidr_blocks=[my_ip]),
        yandex.VpcSecurityGroupIngressArgs(description="http", protocol="TCP", port=80, v4_cidr_blocks=["0.0.0.0/0"]),
        yandex.VpcSecurityGroupIngressArgs(description="app5000", protocol="TCP", port=5000, v4_cidr_blocks=["0.0.0.0/0"]),
    ],
)

# Get image for compute instance
image = yandex.get_compute_image(family="ubuntu-2204-lts")

# Create compute instance
vm = yandex.ComputeInstance(
    "lab-vm",
    name="lab-vm",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(cores=2, core_fraction=20, memory=1),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(image_id=image.id, size=10, type="network-hdd")),
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(subnet_id=subnet.id, nat=True)],
    metadata={"ssh-keys": f"{ssh_user}:{open("/Users/sayfetik/.ssh/id_rsa.pub").read().strip()}"},
)

pulumi.export("public_ip", vm.network_interfaces[0].nat_ip_address)
