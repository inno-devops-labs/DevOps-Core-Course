import pulumi
import pulumi_yandex as yandex
import os


config = pulumi.Config()
project_name = config.get("projectName") or "devops-lab04"
zone = config.get("zone") or "ru-central1-a"
folder_id = config.require("folderId")
ssh_user = config.get("sshUser") or "ubuntu"
ssh_public_key = config.require_secret("sshPublicKey")
image_id = config.get("imageId") or "fd83ica41cade1mj35sr"  # Ubuntu 24.04 LTS v20251222
allowed_ssh_cidr = config.get("allowedSshCidr") or "0.0.0.0/0"
token = config.get_secret("ycToken") or pulumi.Output.from_input(os.environ.get("YC_TOKEN", ""))


# Network — use existing default network (free tier quota: 1 network)
network = yandex.get_vpc_network(name="default", folder_id=folder_id)

subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    zone=zone,
    network_id=network.id,
    folder_id=folder_id,
    v4_cidr_blocks=["10.0.0.0/24"],
)


security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    network_id=network.id,
    folder_id=folder_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH access",
            port=22,
            v4_cidr_blocks=[allowed_ssh_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="App port 5000",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            description="Allow all outbound traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)


vm = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        memory=1,
        core_fraction=20,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=10,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            security_group_ids=[security_group.id],
            nat=True,  # Allocate public IP
        ),
    ],
    metadata=ssh_public_key.apply(
        lambda key: {
            "ssh-keys": f"{ssh_user}:{key}",
        }
    ),
    labels={
        "project": project_name,
        "env": "lab",
        "managed": "pulumi",
    },
)

public_ip = vm.network_interfaces[0].nat_ip_address

pulumi.export("vm_name", vm.name)
pulumi.export("vm_id", vm.id)
pulumi.export("public_ip", public_ip)
pulumi.export(
    "ssh_connection_command",
    public_ip.apply(lambda ip: f"ssh {ssh_user}@{ip}"),
)
pulumi.export("network_id", network.id)
pulumi.export("security_group_id", security_group.id)
