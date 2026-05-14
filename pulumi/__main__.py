import os
import pulumi
import pulumi_yandex as yandex

os.environ["YC_SERVICE_ACCOUNT_KEY_FILE"] = os.path.expanduser("~/key.json")

SSH_PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ7C/mVRl+EokdvvyE8LalEr/6Bki/CGHxL8bhL33xK6 lab04"

# Сеть
network = yandex.VpcNetwork("lab04-network",
    name="lab04-network"
)

# Подсеть
subnet = yandex.VpcSubnet("lab04-subnet",
    name="lab04-subnet",
    zone="ru-central1-a",
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"]
)

# Группа безопасности
sg = yandex.VpcSecurityGroup("lab04-sg",
    name="lab04-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="SSH"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="HTTP"
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="App port"
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ]
)

# Виртуальная машина
vm = yandex.ComputeInstance("lab04-vm",
    name="lab04-vm",
    platform_id="standard-v2",
    zone="ru-central1-a",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd83esfomhq25p2ono90",
            size=10,
            type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id]
        )
    ],
    metadata={
        "ssh-keys": f"ubuntu:{SSH_PUBLIC_KEY}"
    },
    labels={"lab": "lab04"}
)

pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_command", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh ubuntu@{ip}"
))
