import pulumi
import pulumi_yandex as yandex

# --- Configuration ---
config = pulumi.Config()
folder_id = config.require("folder_id")
zone = config.get("zone", "ru-central1-a")

# Your public IP (from your SSH log)
your_public_ip = "188.130.155.186"

# --- 1. Create VPC Network ---
network = yandex.VpcNetwork("lab-network",
    name="lab-network"
)

# --- 2. Create Subnet ---
subnet = yandex.VpcSubnet("lab-subnet",
    name="lab-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=["192.168.10.0/24"]
)

# --- 3. Create Security Group (without rules) ---
security_group = yandex.VpcSecurityGroup("lab-sg",
    name="lab-security-group",
    network_id=network.id,
    # No ingress/egress here!
)

# --- 4. Create Security Group Rules as separate resources ---
# SSH rule (restricted to your IP)
ssh_rule = yandex.VpcSecurityGroupRule("ssh-rule",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=22,
    v4_cidr_blocks=[f"{your_public_ip}/32"],
    description="SSH"
)

# HTTP rule (open to all)
http_rule = yandex.VpcSecurityGroupRule("http-rule",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=80,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="HTTP"
)

# Port 5000 rule (open to all)
app_rule = yandex.VpcSecurityGroupRule("app-rule",
    security_group_binding=security_group.id,
    direction="ingress",
    protocol="TCP",
    port=5000,
    v4_cidr_blocks=["0.0.0.0/0"],
    description="Custom App Port"
)

# Egress rule (all outbound traffic)
egress_rule = yandex.VpcSecurityGroupRule("egress-rule",
    security_group_binding=security_group.id,
    direction="egress",
    protocol="ANY",
    v4_cidr_blocks=["0.0.0.0/0"],
    description="All outbound"
)

# --- 5. Get Latest Ubuntu 22.04 Image ---
ubuntu_image = yandex.get_compute_image(family="ubuntu-2204-lts")

# --- 6. Read SSH Public Key ---
import os
with open(os.path.expanduser("~/.ssh/id_ed25519.pub"), "r") as f:
    ssh_public_key = f.read().strip()

# --- 7. Create VM Instance ---
vm = yandex.ComputeInstance("lab-vm",
    name="lab-vm",
    zone=zone,
    platform_id="standard-v2",
    resources={
        "cores": 2,
        "memory": 1,
        "core_fraction": 20
    },
    boot_disk={
        "initialize_params": {
            "image_id": ubuntu_image.id,
            "size": 10,
            "type": "network-hdd"
        }
    },
    network_interfaces=[{
        "subnet_id": subnet.id,
        "nat": True,
        "security_group_ids": [security_group.id]
    }],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}"
    }
)

# --- 8. Export Outputs ---
pulumi.export("vm_public_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("ssh_command", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh ubuntu@{ip}"
))
