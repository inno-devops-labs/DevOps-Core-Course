"""
Pulumi infrastructure for Lab 04
Creates a VM in Yandex Cloud (equivalent to Terraform configuration)
"""
import pulumi
import pulumi_yandex as yandex

# Get configuration
config = pulumi.Config()
project_name = config.get("project_name", "devops-lab04")
environment = config.get("environment", "dev")
zone = config.get("zone", "ru-central1-a")
folder_id = config.get("folder_id", "b1gs58kbt2o47e40l5cp")  # Yandex Cloud Folder ID
subnet_cidr = config.get("subnet_cidr", "10.0.1.0/24")
allowed_ssh_cidr = config.get("allowed_ssh_cidr", "0.0.0.0/0")
ssh_username = config.get("ssh_username", "ubuntu")

# Read SSH public key
try:
    ssh_public_key_path = config.require("ssh_public_key_path")
    with open(ssh_public_key_path, "r") as f:
        ssh_public_key = f.read().strip()
except Exception as e:
    raise pulumi.RunError(f"Failed to read SSH public key: {e}")

# Get latest Ubuntu image - using hardcoded image ID for now
# Note: pulumi-yandex may have different API, using image ID directly
ubuntu_image_id = "fd8t9g30r3pc23et5krl"  # Ubuntu 22.04 LTS image ID

# Create VPC network
network = yandex.VpcNetwork(
    f"{project_name}-network",
    name=f"{project_name}-network",
    folder_id=folder_id
)

# Create subnet
subnet = yandex.VpcSubnet(
    f"{project_name}-subnet",
    name=f"{project_name}-subnet",
    zone=zone,
    network_id=network.id,
    folder_id=folder_id,
    v4_cidr_blocks=[subnet_cidr]
)

# Create security group
security_group = yandex.VpcSecurityGroup(
    f"{project_name}-sg",
    name=f"{project_name}-sg",
    network_id=network.id,
    folder_id=folder_id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[allowed_ssh_cidr]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="Custom port 5000",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all outbound traffic",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ]
)

# Create compute instance
vm = yandex.ComputeInstance(
    f"{project_name}-vm",
    name=f"{project_name}-vm",
    platform_id="standard-v2",
    zone=zone,
    folder_id=folder_id,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        core_fraction=20,  # Free tier: 20% of vCPU
        memory=1  # 1 GB RAM
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=ubuntu_image_id,
            size=10,  # 10 GB HDD
            type="network-hdd"
        )
    ),
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        security_group_ids=[security_group.id],
        nat=True  # Enable public IP
    )],
    metadata={
        "ssh-keys": f"{ssh_username}:{ssh_public_key}"
    },
    labels={
        "project": project_name,
        "env": environment,
        "managed": "pulumi"
    }
)

# Export outputs
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_private_ip", vm.network_interfaces[0].ip_address)
pulumi.export("vm_id", vm.id)
pulumi.export("ssh_command", pulumi.Output.concat(
    "ssh ", ssh_username, "@", vm.network_interfaces[0].nat_ip_address
))
pulumi.export("network_id", network.id)
pulumi.export("subnet_id", subnet.id)
