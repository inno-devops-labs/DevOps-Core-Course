"""A Python Pulumi program"""

import pulumi
import pulumi_yandex as yandex

cfg = pulumi.Config()

vm_name = cfg.get("vmName") or "lab-vm"
vm_user = cfg.get("vmUser") or "ubuntu"

ssh_allow_cidr = cfg.require("sshAllowCidr")
ssh_public_key_path = cfg.require("sshPublicKeyPath")

subnet_cidr = cfg.get("subnetCidr") or "10.10.0.0/24"

cores = int(cfg.get("cores") or 2)
memory_gb = int(cfg.get("memoryGb") or 2)
core_fraction = int(cfg.get("coreFraction") or 20)

labels = {
    "project": "lab04",
    "tool": "pulumi",
}

# Ubuntu 24.04 image (family)
image = yandex.get_compute_image(family="ubuntu-2404-lts")

net = yandex.VpcNetwork(f"{vm_name}-net", labels=labels)

subnet = yandex.VpcSubnet(
    f"{vm_name}-subnet",
    network_id=net.id,
    zone=cfg.get("yandex:zone") or "ru-central1-a",
    v4_cidr_blocks=[subnet_cidr],
    labels=labels,
)

sg = yandex.VpcSecurityGroup(
    f"{vm_name}-sg",
    network_id=net.id,
    labels=labels,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[ssh_allow_cidr],
            description="SSH from my IP",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="HTTP",
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
            description="App port 5000",
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
            description="Allow all egress",
        )
    ],
)

ip = yandex.VpcAddress(
    f"{vm_name}-ip",
    labels=labels,
    external_ipv4_address=yandex.VpcAddressExternalIpv4AddressArgs(
        zone_id=cfg.get("yandex:zone") or "ru-central1-a"
    ),
)

def ip_addr(ext):
    if isinstance(ext, dict):
        return ext.get("address")
    return getattr(ext, "address", None)

public_ip = ip.external_ipv4_address.apply(ip_addr)

with open(ssh_public_key_path, "r", encoding="utf-8") as f:
    ssh_pub = f.read().strip()

vm = yandex.ComputeInstance(
    vm_name,
    labels=labels,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        memory=memory_gb,
        core_fraction=core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=20,
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            nat_ip_address=public_ip,
            security_group_ids=[sg.id],
        )
    ],
    metadata={
        "ssh-keys": f"{vm_user}:{ssh_pub}",
    },
)

pulumi.export("public_ip", public_ip)
pulumi.export("ssh_command", pulumi.Output.concat("ssh -i ~/.ssh/id_ed25519 ", vm_user, "@", public_ip))
