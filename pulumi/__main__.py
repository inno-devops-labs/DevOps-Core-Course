import pulumi
import pulumi_yandex as yandex

# 1. Сеть
network = yandex.VpcNetwork("lab-net", name="lab-net-pulumi")

# 2. Подсеть
subnet = yandex.VpcSubnet("lab-subnet",
    name="lab-subnet-pulumi",
    zone="ru-central1-a",
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"])

# 3. Образ
ubuntu_image = yandex.get_compute_image(family="ubuntu-2204-lts")

# 4. SSH ключ (проверь путь!)
with open("C:/Users/Bulat/.ssh/id_rsa.pub", "r") as f:
    ssh_key = f.read().strip()

# 5. Машина (без привязки к Security Group)
vm = yandex.ComputeInstance("lab-vm",
    name="lab-vm-pulumi",
    platform_id="standard-v2",
    zone="ru-central1-a",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2,
        core_fraction=20
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=10
        )
    ),
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat=True
    )],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_key}"
    })

# Вывод IP
pulumi.export("instance_external_ip", vm.network_interfaces[0].nat_ip_address)