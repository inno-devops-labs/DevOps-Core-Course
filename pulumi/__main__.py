import os
import pulumi
from pulumi import Config, Output
import pulumi_yandex as yandex

cfg = Config()

zone = cfg.get("zone") or "ru-central1-a"
subnet_cidr = cfg.get("subnetCidr") or "10.10.0.0/24"
my_ip_cidr = cfg.require("myIpCidr")
ssh_user = cfg.get("sshUser") or "ubuntu"
ssh_pubkey_path = cfg.get("sshPublicKeyPath") or os.path.expanduser("$HOME/.ssh/yc_lab.pub")
image_id = cfg.require("imageId")

# VM sizing (same as Terraform)
platform_id = cfg.get("platformId") or "standard-v3"
cores = int(cfg.get("cores") or "2")
core_fraction = int(cfg.get("coreFraction") or "20")
memory_gb = float(cfg.get("memoryGb") or "1")
boot_disk_gb = int(cfg.get("bootDiskGb") or "10")

pubkey = open(ssh_pubkey_path, "r").read().strip()

net = yandex.VpcNetwork("lab-net", name="lab-net")

subnet = yandex.VpcSubnet(
    "lab-subnet",
    name="lab-subnet",
    zone=zone,
    network_id=net.id,
    v4_cidr_blocks=[subnet_cidr],
)

sg = yandex.VpcSecurityGroup(
    "lab-sg",
    name="lab-sg",
    network_id=net.id,
    description="lab security group",
    labels={
        "project": "lab4",
        "iac": "pulumi",
    },
)

# Ingress: SSH 22 from your IP
yandex.VpcSecurityGroupRule(
    "rule-ssh-22",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    description="SSH from my IP",
    v4_cidr_blocks=[my_ip_cidr],
    port=22,
)

# Ingress: HTTP 80 from anywhere
yandex.VpcSecurityGroupRule(
    "rule-http-80",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    description="HTTP",
    v4_cidr_blocks=["0.0.0.0/0"],
    port=80,
)

# Ingress: app 5000 from anywhere
yandex.VpcSecurityGroupRule(
    "rule-app-5000",
    security_group_binding=sg.id,
    direction="ingress",
    protocol="TCP",
    description="App port 5000",
    v4_cidr_blocks=["0.0.0.0/0"],
    port=5000,
)

# Egress: allow all outbound
yandex.VpcSecurityGroupRule(
    "rule-egress-any",
    security_group_binding=sg.id,
    direction="egress",
    protocol="ANY",
    description="Allow all outbound",
    v4_cidr_blocks=["0.0.0.0/0"],
)

vm = yandex.ComputeInstance(
    "lab-vm",
    name="lab-vm",
    zone=zone,
    platform_id=platform_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        core_fraction=core_fraction,
        memory=memory_gb,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=boot_disk_gb,
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
    labels={
        "project": "lab4",
        "iac": "pulumi",
    },
)

public_ip = vm.network_interfaces.apply(lambda nics: nics[0].nat_ip_address)
pulumi.export("public_ip", public_ip)
pulumi.export("ssh_command", Output.concat("ssh -i ~/.ssh/yc_lab ", ssh_user, "@", public_ip))
