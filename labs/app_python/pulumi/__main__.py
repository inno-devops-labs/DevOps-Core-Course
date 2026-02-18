"""A Python Pulumi program"""

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()
project_name = config.get("project_name", "myapp")
ssh_public_key = config.require("ssh_public_key")
allowed_ssh_ip = config.get("allowed_ssh_ip", "0.0.0.0/0")
instance_cores = config.get_int("instance_cores", 2)
instance_memory = config.get_int("instance_memory", 2)
boot_disk_size = config.get_int("boot_disk_size", 20)
zone = config.get("zone", "ru-central1-b")
image_family = config.get("image_family", "ubuntu-2204-lts")
subnet_cidr = config.get("subnet_cidr", "10.0.1.0/24")
labels = {
    "environment": "dev",
    "managed_by": "pulumi"
}


ubuntu_image = yandex.get_compute_image(family=image_family)


vpc_network = yandex.VpcNetwork(
    f"{project_name}-net",
    description=f"VPC for {project_name}",
    labels=labels
)


vpc_subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    description=f"Subnet in {zone}",
    v4_cidr_blocks=[subnet_cidr],
    zone=zone,
    network_id=vpc_network.id,
    labels=labels
)

# --- Create the security group (without rules) ---
security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    description=f"Security group for {project_name}",
    network_id=vpc_network.id,
    labels=labels
)

# --- Ingress rule for SSH (from your IP) ---
yandex.VpcSecurityGroupRule(
    f"{project_name}-sg-ssh",
    security_group_binding=security_group.id,  # Changed from security_group_id
    direction="ingress",
    protocol="TCP",
    port=22,
    v4_cidr_blocks=[allowed_ssh_ip],
    description="SSH access"
)

# --- Ingress rule for HTTP (from anywhere) ---
yandex.VpcSecurityGroupRule(
    f"{project_name}-sg-http",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=80,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="HTTP access"
)

# --- Ingress rule for custom port 5000 (from anywhere) ---
yandex.VpcSecurityGroupRule(
    f"{project_name}-sg-custom",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=5000,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Custom app port"
)

# --- Egress rule to allow all outgoing traffic ---
yandex.VpcSecurityGroupRule(
    f"{project_name}-sg-egress",
    security_group_binding=security_group.id,
    direction="egress",
    protocol="ANY",
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Allow all outgoing"
)

vm = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    description="Smallest free‑tier VM",
    zone=zone,
    labels=labels,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=instance_cores,
        memory=instance_memory,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image.id,
            size=boot_disk_size,
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=vpc_subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}"
    }
)


pulumi.export("instance_public_ip", vm.network_interfaces.apply(lambda nis: nis[0].nat_ip_address))
pulumi.export("instance_id", vm.id)
pulumi.export("ssh_connection_command", vm.network_interfaces.apply(
    lambda nis: f"ssh ubuntu@{nis[0].nat_ip_address}"
))
