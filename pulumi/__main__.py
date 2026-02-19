"""A Python Pulumi program"""

import pulumi
from pulumi import Config
from pulumi_command import local

# Read configuration
config = Config()
vm_name = config.require("vmName")
vm_ip = config.require("vmIp")
ssh_user = config.get("sshUser") or "ubuntu"

# Create local file with VM information
create_file = local.Command(
    "createVmInfoFile",
    create=f"""
    echo "Virtual Machine Information" > vm_info.txt &&
    echo "---------------------------" >> vm_info.txt &&
    echo "VM Name: {vm_name}" >> vm_info.txt &&
    echo "VM IP: {vm_ip}" >> vm_info.txt &&
    echo "SSH Command: ssh {ssh_user}@{vm_ip}" >> vm_info.txt
    """
)

pulumi.export("vm_name", vm_name)
pulumi.export("vm_ip", vm_ip)
pulumi.export("ssh_command", f"ssh {ssh_user}@{vm_ip}")
