"""Lab 4 - Pulumi: GCP VM (same infrastructure as Terraform)."""
import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
project_id = config.require("project_id")
zone = config.get("zone") or "us-central1-a"
ssh_public_key_path = config.require("ssh_public_key_path")

# Read SSH public key
with open(ssh_public_key_path, "r", encoding="utf-8") as f:
    ssh_public_key = f.read().strip()

# Firewall: SSH (22), HTTP (80), app port (5000)
firewall = gcp.compute.Firewall(
    "lab04-vm-firewall",
    name="lab04-vm-firewall",
    network="default",
    allows=[{"protocol": "tcp", "ports": ["22", "80", "5000"]}],
    source_ranges=["0.0.0.0/0"],
    target_tags=["lab04-vm"],
    project=project_id,
)

# VM instance (e2-micro free tier)
vm = gcp.compute.Instance(
    "lab04-vm",
    name="lab04-vm",
    machine_type="e2-micro",
    zone=zone,
    tags=["lab04-vm"],
    boot_disk=gcp.compute.InstanceBootDiskArgs(
        initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
            image="ubuntu-os-cloud/ubuntu-2204-lts",
            size=10,
        )
    ),
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network="default",
            access_configs=[gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()],
        )
    ],
    metadata={
        "ssh-keys": f"ubuntu:{ssh_public_key}",
    },
    labels={
        "lab": "lab04",
    },
    project=project_id,
)

# Outputs
pulumi.export("instance_public_ip", vm.network_interfaces[0].access_configs[0].nat_ip)
pulumi.export(
    "ssh_command",
    vm.network_interfaces[0].access_configs[0].nat_ip.apply(
        lambda ip: f"ssh ubuntu@{ip}"
    ),
)
