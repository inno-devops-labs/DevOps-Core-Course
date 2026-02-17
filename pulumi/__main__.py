import os
import pulumi
import pulumi_yandex as yandex

# === параметры (можно вынести в pulumi.Config, но для лабы ок так) ===
ZONE = os.getenv("YC_ZONE", "ru-central1-a")

SSH_USER = "ubuntu"
# Путь к публичному ключу на твоём Mac
SSH_PUBLIC_KEY_PATH = os.path.expanduser("~/.ssh/id_ed25519.pub")

# Твой IP/32 (как в Terraform). При необходимости обнови.
MY_IP_CIDR = "192.145.30.13/32"

with open(SSH_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
    ssh_pub_key = f.read().strip()

# Берём последний образ Ubuntu по family (как в Terraform data source)
img = yandex.get_compute_image(family="ubuntu-2404-lts")

net = yandex.VpcNetwork("lab04-net", name="lab04-net")

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-subnet",
    network_id=net.id,
    v4_cidr_blocks=["10.10.0.0/24"],
    zone=ZONE,
)

sg = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="lab04-sg",
    network_id=net.id,
    egresses=[
        {
            "protocol": "ANY",
            "description": "Allow all outbound",
            "v4_cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    ingresses=[
        {
            "protocol": "TCP",
            "description": "SSH from my IP",
            "port": 22,
            "v4_cidr_blocks": [MY_IP_CIDR],
        },
        {
            "protocol": "TCP",
            "description": "HTTP",
            "port": 80,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "TCP",
            "description": "App 5000",
            "port": 5000,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
    ],
)

vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
    zone=ZONE,
    platform_id="standard-v1",
    resources={
        # В YC у тебя уже всплывали ограничения: cores должны быть 2 или 4,
        # а память для 2 cores должна быть >= 2GB.
        "cores": 2,
        "memory": 2,
        "core_fraction": 20,
    },
    boot_disk={
        "initialize_params": {
            "image_id": img.image_id,
            "size": 10,
        }
    },
    network_interfaces=[
        {
            "subnet_id": subnet.id,
            "nat": True,  # публичный IP
            "security_group_ids": [sg.id],
        }
    ],
    metadata={
        "ssh-keys": f"{SSH_USER}:{ssh_pub_key}",
    },
)

public_ip = vm.network_interfaces.apply(lambda nis: nis[0]["nat_ip_address"])
pulumi.export("public_ip", public_ip)
pulumi.export("ssh_command", public_ip.apply(lambda ip: f"ssh {SSH_USER}@{ip}"))
