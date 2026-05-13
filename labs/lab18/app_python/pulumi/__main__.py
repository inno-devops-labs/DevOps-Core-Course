"""A Python Pulumi program"""

import pulumi
import pulumi_yandex as yandex
import os

config = pulumi.Config()
zone = config.require("zone")
app_port = config.require_int("appPort")
ssh_user = config.require("sshUser")
ssh_key_path = config.require("sshPublicKeyPath")

with open(os.path.expanduser(ssh_key_path)) as f:
    public_key = f.read().strip()

network = yandex.VpcNetwork("network", name="network")

subnet = yandex.VpcSubnet(
    "subnet",
    name="subnet1",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.10.0/24"]
)

vm_sg = yandex.VpcSecurityGroup(
    "vm-sg",
    description="VM security group",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(port=22, protocol="TCP", v4_cidr_blocks=["0.0.0.0/0"]),
        yandex.VpcSecurityGroupIngressArgs(port=80, protocol="TCP", v4_cidr_blocks=["0.0.0.0/0"]),
        yandex.VpcSecurityGroupIngressArgs(port=app_port, protocol="TCP", v4_cidr_blocks=["0.0.0.0/0"]),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(protocol="ANY", from_port=0, to_port=0, v4_cidr_blocks=["0.0.0.0/0"])
    ]
)

image = yandex.get_compute_image(family="ubuntu-2204-lts")

vm = yandex.ComputeInstance(
    "vm",
    name="pulumi",
    zone=zone,
    resources={"cores": 2, "memory": 2},
    boot_disk={
        "initialize_params": {
            "name": "boot-disk",
            "size": 20,
            "type": "network-hdd",
            "image_id": image.id,
        }
    },
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [vm_sg.id],
    }],
    metadata={"ssh-keys": f"{ssh_user}:{public_key}"}
)

pulumi.export("internal_ip", vm.network_interfaces[0]["ip_address"])
pulumi.export("external_ip", vm.network_interfaces[0]["nat_ip_address"])
