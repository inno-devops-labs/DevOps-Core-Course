"""
Yandex Cloud resources via Pulumi.
Auth: either set token or service account key file before running:
  pulumi config set yandex:token YOUR_TOKEN --secret
  pulumi config set yandex:folderId YOUR_FOLDER_ID
  # or key file:
  pulumi config set yandex:serviceAccountKeyFile /path/to/key.json
"""
import pulumi
import pulumi_yandex as yandex

config = pulumi.Config("yandex")
folder_id = config.require("folderId")  # обязателен: pulumi config set yandex:folderId YOUR_FOLDER_ID

# SSH-ключ — в конфиге проекта (не yandex:), иначе провайдер выдаст "Invalid or unknown key"
# pulumi config set sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"
ssh_public_key = pulumi.Config().get("sshPublicKey") or ""

# ---------------------------
# Сеть
# ---------------------------
network = yandex.VpcNetwork(
    "lab-network",
    folder_id=folder_id,
)

subnet = yandex.VpcSubnet(
    "lab-subnet",
    folder_id=folder_id,
    zone="ru-central1-a",
    network_id=network.id,
    v4_cidr_blocks=["10.0.0.0/24"],
)

# ---------------------------
# Security Group (пустая)
# ---------------------------
sg = yandex.VpcSecurityGroup(
    "lab-sg",
    folder_id=folder_id,
    network_id=network.id,
)

# ---------------------------
# Security Group Rules
# ---------------------------
yandex.VpcSecurityGroupRule(
    "ssh-rule",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    port=22,
    v4_cidr_blocks=["0.0.0.0/0"]
)

yandex.VpcSecurityGroupRule(
    "http-rule",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    port=80,
    v4_cidr_blocks=["0.0.0.0/0"]
)

yandex.VpcSecurityGroupRule(
    "app-rule",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    port=5000,
    v4_cidr_blocks=["0.0.0.0/0"]
)

# ---------------------------
# VM
# ---------------------------
vm_metadata = {"ssh-keys": f"ubuntu:{ssh_public_key}"} if ssh_public_key else None
vm = yandex.ComputeInstance(
    "lab-vm",
    folder_id=folder_id,
    zone="ru-central1-a",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd80293ig2816a78q276",  # Ubuntu 22.04 LTS
        ),
    ),
    metadata=vm_metadata,
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id],
        )
    ],
)

# ---------------------------
# Outputs
# ---------------------------
pulumi.export("public_ip", vm.network_interfaces[0].nat_ip_address)