"""
Lab 4 — Pulumi: same infrastructure as Terraform (VPC, subnet, security group, VM) on Yandex Cloud.
Auth: YANDEX_CLOUD_ID, YANDEX_FOLDER_ID, YANDEX_SERVICE_ACCOUNT_KEY_FILE (or set in Provider below).
"""
# Ensure pkg_resources (from setuptools) is available for pulumi_yandex on Python 3.12+
try:
    import pkg_resources  # noqa: F401
except ImportError:
    import subprocess
    import sys
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "setuptools"],
        capture_output=True,
        timeout=60,
    )
    import pkg_resources  # noqa: F401

import os
import pulumi
import pulumi_yandex as yandex
from pulumi_yandex import get_compute_image


def main() -> None:
    config = pulumi.Config()
    project_name = config.get("project_name") or "devops-lab4"
    zone = config.get("zone") or "ru-central1-a"
    subnet_cidr = config.get("subnet_cidr") or "10.0.1.0/24"
    ssh_allowed_cidr = config.get("ssh_allowed_cidr") or "0.0.0.0/0"
    ssh_user = config.get("ssh_user") or "ubuntu"
    ssh_public_key_path = config.get("ssh_public_key_path") or os.path.expanduser("~/.ssh/id_rsa.pub")

    # Provider: use env vars (set by lab04_evidence.sh) or Pulumi config
    cloud_id = os.environ.get("YANDEX_CLOUD_ID") or config.get("yandex:cloudId")
    folder_id = os.environ.get("YANDEX_FOLDER_ID") or config.get("yandex:folderId")
    key_file = os.environ.get("YANDEX_SERVICE_ACCOUNT_KEY_FILE") or config.get("yandex:serviceAccountKeyFile")
    provider = None
    if cloud_id or folder_id or key_file:
        provider = yandex.Provider(
            "yandex",
            cloud_id=cloud_id or None,
            folder_id=folder_id or None,
            service_account_key_file=key_file or None,
            zone=zone,
        )
        opts = pulumi.ResourceOptions(provider=provider)
    else:
        opts = pulumi.ResourceOptions()

    # Ubuntu 22.04 LTS image
    invoke_opts = pulumi.InvokeOptions(provider=provider) if provider else None
    ubuntu = get_compute_image(family="ubuntu-2204-lts", opts=invoke_opts)

    # VPC Network
    network = yandex.VpcNetwork(
        "network",
        name=f"{project_name}-network",
        opts=opts,
    )

    # Subnet
    subnet = yandex.VpcSubnet(
        "subnet",
        name=f"{project_name}-subnet",
        network_id=network.id,
        zone=zone,
        v4_cidr_blocks=[subnet_cidr],
        opts=opts,
    )

    # Security group: SSH, HTTP, app port 5000, egress any
    sg = yandex.VpcSecurityGroup(
        "sg",
        name=f"{project_name}-sg",
        network_id=network.id,
        ingresses=[
            yandex.VpcSecurityGroupIngressArgs(description="SSH", protocol="TCP", port=22, v4_cidr_blocks=[ssh_allowed_cidr]),
            yandex.VpcSecurityGroupIngressArgs(description="HTTP", protocol="TCP", port=80, v4_cidr_blocks=["0.0.0.0/0"]),
            yandex.VpcSecurityGroupIngressArgs(description="App port", protocol="TCP", port=5000, v4_cidr_blocks=["0.0.0.0/0"]),
        ],
        egresses=[
            yandex.VpcSecurityGroupEgressArgs(description="All outbound", protocol="ANY", v4_cidr_blocks=["0.0.0.0/0"]),
        ],
        opts=opts,
    )

    # SSH key content
    try:
        with open(os.path.expanduser(ssh_public_key_path), "r", encoding="utf-8") as f:
            ssh_key_content = f.read().strip()
    except FileNotFoundError:
        ssh_key_content = ""

    metadata = {}
    if ssh_key_content:
        metadata["ssh-keys"] = f"{ssh_user}:{ssh_key_content}"

    # Compute instance (same specs as Terraform: standard-v2, 2 cores 20%, 1 GB, 10 GB disk)
    vm = yandex.ComputeInstance(
        "vm",
        name=f"{project_name}-vm",
        platform_id="standard-v2",
        zone=zone,
        resources=yandex.ComputeInstanceResourcesArgs(
            cores=2,
            core_fraction=20,
            memory=1,
        ),
        boot_disk=yandex.ComputeInstanceBootDiskArgs(
            initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
                image_id=ubuntu.image_id,
                size=10,
                type="network-hdd",
            ),
        ),
        network_interfaces=[
            yandex.ComputeInstanceNetworkInterfaceArgs(
                subnet_id=subnet.id,
                nat=True,
                security_group_ids=[sg.id],
            ),
        ],
        metadata=metadata,
        labels={
            "project": project_name,
            "env": "dev",
            "managed": "pulumi",
        },
        opts=opts,
    )

    # Outputs
    vm_private_ip = vm.network_interfaces.apply(lambda nics: nics[0].ip_address if nics else None)
    vm_public_ip = vm.network_interfaces.apply(lambda nics: nics[0].nat_ip_address if nics else None)
    pulumi.export("network_id", network.id)
    pulumi.export("subnet_id", subnet.id)
    pulumi.export("security_group_id", sg.id)
    pulumi.export("vm_id", vm.id)
    pulumi.export("vm_private_ip", vm_private_ip)
    pulumi.export("vm_public_ip", vm_public_ip)
    pulumi.export("ssh_command", vm_public_ip.apply(lambda ip: f"ssh {ssh_user}@{ip}" if ip else ""))


if __name__ == "__main__":
    main()
