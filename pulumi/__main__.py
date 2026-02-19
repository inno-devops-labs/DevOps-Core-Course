import os
import pulumi
import pulumi_yandex as yandex

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
config = pulumi.Config()
folder_id = config.require("folderId")
zone = config.get("zone") or "ru-central1-a"
vm_name = config.get("vmName") or "lab4-vm"
vm_user = config.get("vmUser") or "ubuntu"
ssh_key_path = config.require("sshKeyPath")
my_ip = config.require("myIp")

ssh_key_file = os.path.expanduser(ssh_key_path)
with open(ssh_key_file, "r") as f:
    ssh_public_key = f.read().strip()

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
network = yandex.VpcNetwork(
    "lab4-network",
    folder_id=folder_id,
    name="lab4-network",
)

subnet = yandex.VpcSubnet(
    "lab4-subnet",
    folder_id=folder_id,
    name="lab4-subnet",
    network_id=network.id,
    v4_cidr_blocks=["10.0.0.0/24"],
    zone=zone,
)

# ---------------------------------------------------------------------------
# Security Group
# ---------------------------------------------------------------------------
sg = yandex.VpcSecurityGroup(
    "lab4-sg",
    folder_id=folder_id,
    network_id=network.id,
    name="lab4-sg",
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH from my IP",
            from_port=22,
            to_port=22,
            protocol="TCP",
            v4_cidr_blocks=[my_ip],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            from_port=80,
            to_port=80,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="App port",
            from_port=5000,
            to_port=5000,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            from_port=-1,
            to_port=-1,
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

# ---------------------------------------------------------------------------
# Compute Instance
# ---------------------------------------------------------------------------
instance = yandex.ComputeInstance(
    "lab4-vm",
    folder_id=folder_id,
    name=vm_name,
    platform_id="standard-v1",
    zone=zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        core_fraction=20, 
        memory=2,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd804teg9bthv0h96s8v", 
            size=10,
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[sg.id],
        ),
    ],
    metadata={"ssh-keys": f"{vm_user}:{ssh_public_key}"},
)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("public_ip", instance.network_interfaces[0].nat_ip_address)
pulumi.export("private_ip", instance.network_interfaces[0].ip_address)
pulumi.export("vm_id", instance.id)
pulumi.export("ssh_command", instance.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh {vm_user}@{ip}"
))