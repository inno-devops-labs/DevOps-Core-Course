import pulumi
import pulumi_yandex as yc
from pulumi import Config

config = Config()

cloud_id = config.require("cloudId")
folder_id = config.require("folderId")
zone = config.require("zone")
my_ip = config.require("myIp")

provider = yc.Provider(
    "yc-provider",
    cloud_id=cloud_id,
    folder_id=folder_id,
    zone=zone,
    service_account_key_file="authorized_key.json"
)

network = yc.VpcNetwork(
    "net",
    name="net",
    opts=pulumi.ResourceOptions(provider=provider)
)

subnet = yc.VpcSubnet(
    "subnet",
    name="subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["10.0.0.0/24"],
    opts=pulumi.ResourceOptions(provider=provider)
)

# Security Group
security_group = yc.VpcSecurityGroup(
    "sg",
    network_id=network.id,
    ingress=[
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH",
            v4_cidr_blocks=[my_ip],
            port=22
        ),
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=80
        ),
        yc.VpcSecurityGroupIngressArgs(
            protocol="TCP",
            description="App 5000",
            v4_cidr_blocks=["0.0.0.0/0"],
            port=5000
        ),
    ],
    egress=[
        yc.VpcSecurityGroupEgressArgs(
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    opts=pulumi.ResourceOptions(provider=provider)
)

# Image
image = yc.get_compute_image(family="ubuntu-2204-lts")

# VM
vm = yc.ComputeInstance(
    "vm",
    name="pulumi-vm",
    platform_id="standard-v2",
    zone=zone,
    resources=yc.ComputeInstanceResourcesArgs(
        cores=2,
        memory=2
    ),
    boot_disk=yc.ComputeInstanceBootDiskArgs(
        initialize_params=yc.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image.id
        )
    ),
    network_interfaces=[
        yc.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id]
        )
    ],
    metadata={
        "ssh-keys": f"ubuntu:{open('C:/Users/kve10/.ssh/id_ed25519.pub').read()}"
    },
    opts=pulumi.ResourceOptions(provider=provider)
)

pulumi.export("public_ip", vm.network_interfaces.apply(lambda ni: ni[0].nat_ip_address))
pulumi.export("internal_ip", vm.network_interfaces.apply(lambda ni: ni[0].ip_address))
