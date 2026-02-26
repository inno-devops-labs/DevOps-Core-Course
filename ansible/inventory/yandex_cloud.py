#!/usr/bin/env python3
import json
import subprocess
import sys

def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True)

def main() -> None:
    # Uses current 'yc' CLI auth/profile (you already configured it)
    data = sh("yc", "compute", "instance", "list", "--format", "json")
    instances = json.loads(data)

    hosts = []
    hostvars = {}

    for vm in instances:
        nis = vm.get("network_interfaces") or []
        if not nis:
            continue

        p4 = (nis[0].get("primary_v4_address") or {})
        nat = (p4.get("one_to_one_nat") or {})
        public_ip = nat.get("address")
        private_ip = p4.get("address")

        ip = public_ip or private_ip
        if not ip:
            continue

        name = vm.get("name") or ip
        hosts.append(name)
        hostvars[name] = {
            "ansible_host": ip,
            "ansible_user": "ubuntu",
            "ansible_python_interpreter": "/usr/bin/python3",
            "yc_instance_id": vm.get("id"),
        }

    inventory = {
        "_meta": {"hostvars": hostvars},
        "all": {"children": ["webservers"]},
        "webservers": {"hosts": hosts},
    }

    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
