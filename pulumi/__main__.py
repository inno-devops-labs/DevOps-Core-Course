import pulumi
import pulumi_yandex as yandex

# Read configuration (set via pulumi config)
config = pulumi.Config()
cloud_id = config.require("cloud_id")
folder_id = config.require("folder_id")
zone = config.get("zone") or "ru-central1-a"
public_key_path = config.get("public_key_path") or "~/.ssh/id_rsa.pub"

# Read SSH public key file
with open(public_key_path, "r") as f:
    ssh_public_key = f.read().strip()

# Get Ubuntu image
image = yandex.get_compute_image(family="ubuntu-2404-lts-oslogin")

# Create VPC network
network = yandex.VpcNetwork("lab-network")

# Create subnet
subnet = yandex.VpcSubnet("lab-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.10.0/24"])

# Create security group
security_group = yandex.VpcSecurityGroup("lab-sg",
    network_id=network.id,
    description="Allow SSH, HTTP, and app port 5000",
    ingress=[
        yandex.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH",
            port=22,
            v4_cidr_blocks=["0.0.0.0/0"],
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
    egress=[yandex.VpcSecurityGroupEgressArgs(
        protocol="ANY",
        description="Allow all outbound",
        v4_cidr_blocks=["0.0.0.0/0"],
    )])

# Create VM instance
vm = yandex.ComputeInstance("lab-vm",
    zone=zone,
    platform_id="standard-v2",
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
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        security_group_ids=[security_group.id],
        nat=True,
    )],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}",
    })

# Export public IP
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ubuntu@", vm.network_interfaces[0].nat_ip_address))