import os

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
project_name = config.get("projectName") or "devops-lab04"
zone = config.get("zone") or "ru-central1-a"
allowed_ssh_cidr = config.get("allowedSshCidr") or "0.0.0.0/0"

ubuntu = yandex.get_compute_image(family="ubuntu-2404-lts")

network_name = config.get("networkName") or "default"
network = yandex.get_vpc_network(name=network_name)

subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
)

sg = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    network_id=network.id,
    ingresses=[
        {"protocol": "TCP", "port": 22, "v4_cidr_blocks": [allowed_ssh_cidr]},
        {"protocol": "TCP", "port": 80, "v4_cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "TCP", "port": 5000, "v4_cidr_blocks": ["0.0.0.0/0"]},
    ],
    egresses=[
        {"protocol": "ANY", "v4_cidr_blocks": ["0.0.0.0/0"]},
    ],
)

ssh_key_path = os.path.expanduser("~/.ssh/id_rsa.pub")
with open(ssh_key_path) as f:
    public_key = f.read().strip()

instance = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    platform_id="standard-v2",
    zone=zone,
    resources={"cores": 2, "memory": 1, "core_fraction": 20},
    boot_disk={"initialize_params": {
        "image_id": ubuntu.id,
        "size": 10,
        "type": "network-hdd",
    }},
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [sg.id],
    }],
    metadata={"ssh-keys": f"ubuntu:{public_key}"},
)

pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("ssh_command", instance.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh -i ~/.ssh/id_rsa ubuntu@{ip}"
))
