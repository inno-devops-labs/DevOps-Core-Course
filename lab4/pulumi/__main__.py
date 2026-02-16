"""Pulumi program for Lab 04 Task 2 (Yandex Cloud)."""

from pathlib import Path
from typing import Any

import pulumi
import pulumi_yandex as yandex


def get_field(value: Any, field: str) -> Any:
    """Read attribute from dict-like or object-like provider values."""
    if isinstance(value, dict):
        return value.get(field)
    return getattr(value, field, None)


def first_item(values: Any) -> Any:
    """Get first item from list-like provider values."""
    if isinstance(values, list):
        return values[0] if values else None
    if isinstance(values, dict):
        if 0 in values:
            return values[0]
        if "0" in values:
            return values["0"]
        # Some providers may return a single object instead of a list.
        return values
    return None


config = pulumi.Config()

cloud_id = config.require("cloudId")
folder_id = config.require("folderId")
zone = config.get("zone") or "ru-central1-d"
service_account_key_file = config.require("serviceAccountKeyFile")

vm_name = config.get("vmName") or "lab04-pulumi-vm"
network_name = config.get("networkName") or "lab04-network"
subnet_name = config.get("subnetName") or "lab04-subnet"
security_group_name = config.get("securityGroupName") or "lab04-security-group"
subnet_cidr_block = config.get("subnetCidrBlock") or "10.10.0.0/24"

ssh_allowed_cidr = config.require("sshAllowedCidr")
ssh_user = config.get("sshUser") or "ubuntu"
ssh_public_key_path = config.require("sshPublicKeyPath")

image_family = config.get("imageFamily") or "ubuntu-2204-lts"
cores = int(config.get("cores") or "2")
core_fraction = int(config.get("coreFraction") or "20")
memory = float(config.get("memory") or "1")
boot_disk_size = int(config.get("bootDiskSize") or "10")
boot_disk_type = config.get("bootDiskType") or "network-hdd"
preemptible = (config.get("preemptible") or "false").lower() == "true"

# When set, reuse network/subnet of an existing instance.
# This helps when folder has strict VPC network quotas.
existing_instance_id_for_network = config.get("existingInstanceIdForNetwork")

labels = {"managed_by": "pulumi", "lab": "lab04"}
ssh_public_key = Path(ssh_public_key_path).expanduser().read_text(encoding="utf-8").strip()

provider = yandex.Provider(
    "yc-provider",
    cloud_id=cloud_id,
    folder_id=folder_id,
    zone=zone,
    service_account_key_file=service_account_key_file,
)
res_opts = pulumi.ResourceOptions(provider=provider)
invoke_opts = pulumi.InvokeOptions(provider=provider)

image = yandex.get_compute_image_output(
    family=image_family,
    opts=invoke_opts,
)

if existing_instance_id_for_network:
    network_source = yandex.get_compute_instance_output(
        instance_id=existing_instance_id_for_network,
        opts=invoke_opts,
    )
    subnet_id = network_source.network_interfaces.apply(
        lambda items: get_field(first_item(items), "subnet_id") if items else None
    )
    existing_subnet = yandex.get_vpc_subnet_output(
        subnet_id=subnet_id,
        opts=invoke_opts,
    )
    network_id = existing_subnet.network_id
else:
    network = yandex.VpcNetwork(
        "lab04-network",
        folder_id=folder_id,
        name=network_name,
        labels=labels,
        opts=res_opts,
    )
    subnet = yandex.VpcSubnet(
        "lab04-subnet",
        folder_id=folder_id,
        name=subnet_name,
        zone=zone,
        network_id=network.id,
        v4_cidr_blocks=[subnet_cidr_block],
        labels=labels,
        opts=res_opts,
    )
    subnet_id = subnet.id
    network_id = network.id

security_group = yandex.VpcSecurityGroup(
    "lab04-security-group",
    folder_id=folder_id,
    name=security_group_name,
    description="Allow SSH from trusted CIDR, HTTP, and port 5000.",
    network_id=network_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH from trusted address only",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[ssh_allowed_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP from anywhere",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Application port 5000 from anywhere",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound traffic",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    opts=res_opts,
)

public_address = yandex.VpcAddress(
    "lab04-public-ip",
    folder_id=folder_id,
    name=f"{vm_name}-public-ip",
    external_ipv4_address=yandex.VpcAddressExternalIpv4AddressArgs(
        zone_id=zone,
    ),
    opts=res_opts,
)

public_ip = public_address.external_ipv4_address.apply(
    lambda items: get_field(first_item(items), "address") if items else None
)

vm = yandex.ComputeInstance(
    "lab04-vm",
    folder_id=folder_id,
    name=vm_name,
    zone=zone,
    platform_id="standard-v2",
    allow_stopping_for_update=True,
    labels=labels,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        memory=memory,
        core_fraction=core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=boot_disk_size,
            type=boot_disk_type,
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet_id,
            nat=True,
            nat_ip_address=public_ip,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={
        "ssh-keys": f"{ssh_user}:{ssh_public_key}",
    },
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(
        preemptible=preemptible
    ),
    opts=res_opts,
)

pulumi.export("vmId", vm.id)
pulumi.export(
    "vmInternalIp",
    vm.network_interfaces.apply(
        lambda items: get_field(first_item(items), "ip_address") if items else None
    ),
)
pulumi.export("vmPublicIp", public_ip)
pulumi.export("sshCommand", pulumi.Output.concat("ssh ", ssh_user, "@", public_ip))
