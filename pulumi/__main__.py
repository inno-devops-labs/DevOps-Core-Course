import pulumi
import pulumi_yandex as yandex
import os

vpc_network = yandex.VpcNetwork(
    "main-network",
    name="main-network"
)

subnet = yandex.VpcSubnet(
    "main-subnet",
    zone="ru-central1-a",
    network_id=vpc_network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
    name="main-subnet"
)

security_group = yandex.VpcSecurityGroup(
    "web-sg",
    network_id=vpc_network.id,
    name="web-sg",
    description="Allow SSH and HTTP"
)

ssh_rule = yandex.VpcSecurityGroupRule(
    "ssh-rule",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=22,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Allow SSH"
)

http_rule = yandex.VpcSecurityGroupRule(
    "http-rule",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=80,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Allow HTTP"
)

egress_rule = yandex.VpcSecurityGroupRule(
    "egress-rule",
    security_group_binding=security_group.id,
    direction="egress",
    protocol="ANY",
    from_port=0,
    to_port=65535,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Allow all outbound"
)

ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519.pub")

with open(ssh_key_path, "r") as f:
    ssh_public_key = f.read().strip()

instance = yandex.ComputeInstance(
    "web-server",
    name="web-server",
    zone="ru-central1-a",
    platform_id="standard-v2",

    resources={
        "cores": 2,
        "memory": 2,
    },

    boot_disk={
        "initialize_params": {
            "image_id": "fd84n8eontaojc77hp0u",  # Ubuntu 22.04 LTS
            "type": "network-hdd",
            "size": 10,
        }
    },

    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [security_group.id],
    }],

    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}"
    }
)

pulumi.export("public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("instance_id", instance.id)