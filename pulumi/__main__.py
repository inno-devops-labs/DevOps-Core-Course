import pulumi_yandex as yandex

import pulumi

config = pulumi.Config()
project_name = config.get("project_name") or "lab04-devops"
environment = config.get("environment") or "dev"
zone = config.get("zone") or "ru-central1-a"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/id_rsa.pub"

import os

ssh_key_path = os.path.expanduser(ssh_public_key_path)
try:
    with open(ssh_key_path, "r") as f:
        ssh_public_key = f.read().strip()
except FileNotFoundError:
    pulumi.log.warn(f"SSH public key not found at {ssh_key_path}, using placeholder")
    ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD... placeholder"

network = yandex.VpcNetwork(
    "lab-network", name=f"{project_name}-network", description="Network for Lab 04"
)

subnet = yandex.VpcSubnet(
    "lab-subnet",
    name=f"{project_name}-subnet",
    description="Subnet for Lab 04",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.128.0.0/24"],
)

security_group = yandex.VpcSecurityGroup(
    "lab-sg",
    name=f"{project_name}-sg",
    description="Security group for Lab 04 VM",
    network_id=network.id,
    ingress=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow SSH",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=22,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80,
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="Allow custom app",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000,
        ),
    ],
    egress=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outgoing traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

ubuntu_image = yandex.get_compute_image(family="ubuntu-2204-lts")

vm_instance = yandex.ComputeInstance(
    "lab-vm",
    name=f"{project_name}-vm",
    hostname=f"{project_name}-vm",
    zone=zone,
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id, size=10, type="network-hdd"
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id, nat=True, security_group_ids=[security_group.id]
        )
    ],
    metadata={"ssh-keys": f"ubuntu:{ssh_public_key}"},
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(preemptible=True),
    labels={
        "project": project_name,
        "environment": environment,
        "managed_by": "pulumi",
        "lab": "lab04",
    },
)

pulumi.export("vm_id", vm_instance.id)
pulumi.export("vm_name", vm_instance.name)
pulumi.export("vm_external_ip", vm_instance.network_interfaces[0].nat_ip_address)
pulumi.export("vm_internal_ip", vm_instance.network_interfaces[0].ip_address)
pulumi.export("vm_fqdn", vm_instance.fqdn)
pulumi.export("vm_status", vm_instance.status)
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
pulumi.export("security_group_id", security_group.id)
pulumi.export("zone", zone)

pulumi.export(
    "ssh_connection_command",
    vm_instance.network_interfaces[0].nat_ip_address.apply(
        lambda ip: f"ssh ubuntu@{ip}"
    ),
)

pulumi.export(
    "security_rules",
    {
        "ssh": {"port": 22, "protocol": "TCP"},
        "http": {"port": 80, "protocol": "TCP"},
        "app": {"port": 5000, "protocol": "TCP"},
    },
)

pulumi.export(
    "resource_labels",
    {
        "project": project_name,
        "environment": environment,
        "managed_by": "pulumi",
        "lab": "lab04",
    },
)

pulumi.log.info(f"Infrastructure deployment complete!")
pulumi.log.info(f"VM: {project_name}-vm")
pulumi.log.info(f"Zone: {zone}")
