import os
import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
zone = config.get("zone") or "ru-central1-a"
ssh_user = config.get("ssh_user") or "ubuntu"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"

with open(os.path.expanduser(ssh_public_key_path)) as f:
    ssh_public_key = f.read().strip()

image = yandex.get_compute_image(family="ubuntu-2404-lts-oslogin")

network = yandex.VpcNetwork("lab4-network")

subnet = yandex.VpcSubnet(
    "lab4-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
)

security_group = yandex.VpcSecurityGroup(
    "lab4-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP", port=22, v4_cidr_blocks=["0.0.0.0/0"], description="SSH"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP", port=80, v4_cidr_blocks=["0.0.0.0/0"], description="HTTP"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Python app",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=8001,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Go/bonus app",
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound",
        ),
    ],
)

vm = yandex.ComputeInstance(
    "lab4-vm",
    platform_id="standard-v2",
    zone=zone,
    labels={"project": "devops-lab4", "env": "dev"},
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2, memory=2, core_fraction=20
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id, size=10, type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={"ssh-keys": f"{ssh_user}:{ssh_public_key}"},
)

pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", vm.name)
pulumi.export(
    "ssh_connection",
    vm.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh {ssh_user}@{ip}"
    ),
)
