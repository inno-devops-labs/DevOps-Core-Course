import pulumi
import pulumi_yandex as yandex

from pathlib import Path

cfg = pulumi.Config()

# === Terraform parity defaults ===
zone = cfg.get("zone") or "ru-central1-a"
subnet_cidr = cfg.get("subnetCidr") or "10.10.0.0/24"

platform_id = cfg.get("platformId") or "standard-v2"
cores = int(cfg.get("cores") or 2)
memory_gb = int(cfg.get("memoryGb") or 1)
core_fraction = int(cfg.get("coreFraction") or 20)

disk_gb = int(cfg.get("diskGb") or 10)
disk_type = cfg.get("diskType") or "network-hdd"

ssh_user = cfg.get("sshUser") or "ubuntu"
ssh_allow_cidr = cfg.require("sshAllowCidr")

# public key path (for metadata)
ssh_pubkey_path = cfg.get("sshPublicKeyPath") or str(Path.home() / ".ssh/yc-lab04.pub")
# private key path (for ssh -i). If not provided, infer by stripping ".pub"
ssh_privkey_path = cfg.get("sshPrivateKeyPath") or ssh_pubkey_path.removesuffix(".pub")

image_family = cfg.get("imageFamily") or "ubuntu-2204-lts"

pubkey = Path(ssh_pubkey_path).expanduser().read_text(encoding="utf-8").strip()
img = yandex.get_compute_image(family=image_family)

net = yandex.VpcNetwork("lab04-net")

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    network_id=net.id,
    zone=zone,
    v4_cidr_blocks=[subnet_cidr],
)

sg = yandex.VpcSecurityGroup(
    "lab04-sg",
    network_id=net.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH from my IP",
            v4_cidr_blocks=[ssh_allow_cidr],
            port=22,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="App port 5000",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000,
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all egress",
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

vm = yandex.ComputeInstance(
    "lab04-vm",
    zone=zone,
    platform_id=platform_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        memory=memory_gb,
        core_fraction=core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=img.id,
            size=disk_gb,
            type=disk_type,
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id],
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{pubkey}",
    },
)

public_ip = vm.network_interfaces.apply(lambda nis: nis[0]["nat_ip_address"] if nis else None)

pulumi.export("public_ip", public_ip)
pulumi.export("ssh_cmd", pulumi.Output.concat("ssh -i ", ssh_privkey_path, " ", ssh_user, "@", public_ip))
pulumi.export("http_url", pulumi.Output.concat("http://", public_ip))
