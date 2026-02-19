"""
Pulumi program to provision a local VirtualBox Ubuntu VM.
Equivalent to the Terraform null_resource approach.
Uses pulumi_command.local.Command with environment variables to pass
parameters to PowerShell scripts (avoids quoting / Unicode path issues).
"""

import os
import shutil
import tempfile
import pulumi
from pulumi_command import local

# ── Config ──────────────────────────────────────────────────────────────────
config      = pulumi.Config()
vm_name     = config.get("vm_name")     or "ubuntu-pulumi"
vm_cpus     = config.get("vm_cpus")     or "2"
vm_memory   = config.get("vm_memory")   or "1024"
host_only   = config.get("host_only_adapter") or "VirtualBox Host-Only Ethernet Adapter"
vboxmanage  = config.get("vboxmanage")  or r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
box_url     = config.get("box_url")     or (
    "https://app.vagrantup.com/bento/boxes/ubuntu-22.04"
    "/versions/202407.23.0/providers/virtualbox/amd64/vagrant.box"
)

# Copy scripts to an ASCII-safe temp directory (avoids Cyrillic in path)
script_dir  = os.path.dirname(os.path.abspath(__file__))
tmp_scripts = os.path.join(tempfile.gettempdir(), "pulumi_vbox_scripts")
os.makedirs(tmp_scripts, exist_ok=True)
for name in ("create_vm.ps1", "destroy_vm.ps1"):
    src = os.path.join(script_dir, "scripts", name)
    dst = os.path.join(tmp_scripts, name)
    shutil.copy2(src, dst)

create_ps1  = os.path.join(tmp_scripts, "create_vm.ps1")
destroy_ps1 = os.path.join(tmp_scripts, "destroy_vm.ps1")
cache_dir   = os.path.join(tempfile.gettempdir(), "pulumi_vbox_cache")

# ── Shared env vars for scripts ──────────────────────────────────────────────
env = {
    "VBOX_MANAGE":    vboxmanage,
    "VM_NAME":        vm_name,
    "BOX_URL":        box_url,
    "VM_MEMORY":      str(vm_memory),
    "VM_CPUS":        str(vm_cpus),
    "HOST_ONLY":      host_only,
    "CACHE_DIR":      cache_dir,
}

# ── Create VM ────────────────────────────────────────────────────────────────
vm = local.Command(
    "ubuntu-vm",
    create=f"powershell -ExecutionPolicy Bypass -File {create_ps1}",
    delete=f"powershell -ExecutionPolicy Bypass -File {destroy_ps1}",
    environment=env,
)

# ── Outputs ──────────────────────────────────────────────────────────────────
pulumi.export("vm_name",     vm_name)
pulumi.export("ssh_command", f"ssh -p 2223 vagrant@127.0.0.1  # password: vagrant")
pulumi.export("host_only_ip_cmd",
    f'& "{vboxmanage}" guestproperty get {vm_name} /VirtualBox/GuestInfo/Net/1/V4/IP')
