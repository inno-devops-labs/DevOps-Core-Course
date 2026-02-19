import pulumi
import pulumi_yandex as yandex

cfg = pulumi.Config()

zone = cfg.get("zone") or "ru-central1-a"
ssh_user = cfg.get("sshUser") or "ubuntu"
my_ssh_cidr = cfg.require("mySshCidr")          # "1.2.3.4/32"
ssh_pubkey_path = cfg.require("sshPublicKeyPath")
image_id = cfg.require("imageId")

with open(ssh_pubkey_path, "r", encoding="utf-8") as f:
    pubkey = f.read().strip()

net = yandex.VpcNetwork("lab04-net")

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    network_id=net.id,
    zone=zone,
    v4_cidr_blocks=["10.10.0.0/24"],
)

sg = yandex.VpcSecurityGroup(
    "lab04-sg",
    network_id=net.id,
)
# SSH 22 только с твоего IP
yandex.VpcSecurityGroupRule(
    "lab04-sg-ssh",
    security_group_binding=sg.id,
    direction="ingress",
    description="SSH from my IP",
    protocol="TCP",
    v4_cidr_blocks=[my_ssh_cidr],
    port=22,
)

# HTTP 80
yandex.VpcSecurityGroupRule(
    "lab04-sg-http",
    security_group_binding=sg.id,
    direction="ingress",
    description="HTTP",
    protocol="TCP",
    v4_cidr_blocks=["0.0.0.0/0"],
    port=80,
)

# App 5000
yandex.VpcSecurityGroupRule(
    "lab04-sg-5000",
    security_group_binding=sg.id,
    direction="ingress",
    description="App 5000",
    protocol="TCP",
    v4_cidr_blocks=["0.0.0.0/0"],
    port=5000,
)

# Egress all
yandex.VpcSecurityGroupRule(
    "lab04-sg-egress",
    security_group_binding=sg.id,
    direction="egress",
    description="Allow all egress",
    protocol="ANY",
    v4_cidr_blocks=["0.0.0.0/0"],
)
vm = yandex.ComputeInstance(
    "lab04-vm",
    name="lab04-vm",
    zone=zone,
    platform_id="standard-v2",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=2,
        core_fraction=20,
        memory=1,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id=image_id,
            size=10,
            type="network-hdd",
        )
    ),
    network_interfaces=[yandex.ComputeInstanceNetworkInterfaceArgs(
        subnet_id=subnet.id,
        nat=True,
        security_group_ids=[sg.id],
    )],
    metadata={
        "ssh-keys": f"{ssh_user}:{pubkey}",
    },
)
pulumi.export(
    "public_ip",
    vm.network_interfaces.apply(lambda nics: nics[0]["nat_ip_address"])
)

pulumi.export(
    "ssh_command",
    pulumi.Output.concat(
        "ssh ", ssh_user, "@",
        vm.network_interfaces.apply(lambda nics: nics[0]["nat_ip_address"])
    )
)