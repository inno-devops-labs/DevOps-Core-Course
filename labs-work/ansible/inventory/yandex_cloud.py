#!/usr/bin/env python3

import json
import os
import subprocess
import sys


FOLDER_ID = os.environ.get("YC_FOLDER_ID", "<YOUR_FOLDER_ID>")


def yc_list_instances():
    cmd = [
        "yc", "compute", "instance", "list",
        "--folder-id", FOLDER_ID,
        "--format", "json",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("Error: 'yc' CLI not found. Install it first.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error calling yc: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def build_inventory(instances):
    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"children": ["ungrouped", "webservers"]},
        "webservers": {"hosts": []},
        "ungrouped": {"hosts": []},
    }

    for inst in instances:
        if inst.get("status") != "RUNNING":
            continue

        name = inst.get("name", inst["id"])
        labels = inst.get("labels", {})

        # Extract public NAT IP
        nat_ip = None
        for iface in inst.get("network_interfaces", []):
            addr = iface.get("primary_v4_address", {})
            nat = addr.get("one_to_one_nat", {})
            nat_ip = nat.get("address")
            if nat_ip:
                break

        if not nat_ip:
            continue

        inventory["_meta"]["hostvars"][name] = {
            "ansible_host": nat_ip,
            "ansible_user": "ubuntu",
            "ansible_ssh_private_key_file": "~/.ssh/devops-lab04",
        }

        if labels.get("project") == "devops-course":
            inventory["webservers"]["hosts"].append(name)
        else:
            inventory["ungrouped"]["hosts"].append(name)

    return inventory


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        instances = yc_list_instances()
        print(json.dumps(build_inventory(instances), indent=2))
    elif len(sys.argv) == 2 and sys.argv[1] == "--host":
        print(json.dumps({}))
    else:
        print(json.dumps({"_meta": {"hostvars": {}}}))


if __name__ == "__main__":
    main()
