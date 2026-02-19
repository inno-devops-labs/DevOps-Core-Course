"""Lab 04 — Yandex Cloud VM with Pulumi (Python)."""

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
zone = config.get("zone") or "ru-central1-a"
vm_user = config.get("vmUser") or "ubuntu"
ssh_public_key = config.require("sshPublicKey")

# --- Network ---

network = yandex.VpcNetwork(
    "lab04-network",
    name="lab04-network",
    labels={"project": "devops-lab04"},
)

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="lab04-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.1.0/24"],
    labels={"project": "devops-lab04"},
)

# --- Security Group ---

security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="lab04-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="App port",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    labels={"project": "devops-lab04"},
)

# --- Compute Instance ---

image = yandex.get_compute_image(family="ubuntu-2404-lts")

instance = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
    platform_id="standard-v2",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        ),
    ],
    metadata={
        "ssh-keys": f"{vm_user}:{ssh_public_key}",
    },
    labels={
        "project": "devops-lab04",
        "env": "dev",
    },
)

# --- Outputs ---

pulumi.export("vm_public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_name", instance.name)
pulumi.export(
    "ssh_command",
    pulumi.Output.concat("ssh ", vm_user, "@", instance.network_interfaces[0].nat_ip_address),
)
