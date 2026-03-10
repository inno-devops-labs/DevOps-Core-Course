#!/usr/bin/env python3
"""
Yandex Cloud Dynamic Inventory for Ansible.
Queries Yandex Cloud Compute API to discover running VMs.

Requirements:
  pip install yandexcloud grpcio protobuf

Environment variables:
  YC_TOKEN    - Yandex Cloud OAuth token
  YC_FOLDER_ID - Yandex Cloud folder ID
"""

import json
import os
import sys


def get_inventory():
    """Query Yandex Cloud for running VMs and return Ansible inventory."""
    token = os.environ.get("YC_TOKEN", "")
    folder_id = os.environ.get("YC_FOLDER_ID", "")

    if not token or not folder_id:
        # Return empty inventory if credentials not set
        return {
            "_meta": {"hostvars": {}},
            "all": {"hosts": [], "vars": {}},
            "webservers": {"hosts": []},
        }

    try:
        import yandexcloud
        from yandex.cloud.compute.v1.instance_service_pb2 import ListInstancesRequest
        from yandex.cloud.compute.v1.instance_service_pb2_grpc import InstanceServiceStub

        sdk = yandexcloud.SDK(token=token)
        service = sdk.client(InstanceServiceStub)

        response = service.List(ListInstancesRequest(folder_id=folder_id))

        hosts = {}
        webservers = []

        for instance in response.instances:
            # Only include running instances
            if instance.status != 2:  # RUNNING = 2
                continue

            # Get public IP
            public_ip = None
            for iface in instance.network_interfaces:
                if iface.primary_v4_address.one_to_one_nat.address:
                    public_ip = iface.primary_v4_address.one_to_one_nat.address
                    break

            if not public_ip:
                continue

            hostname = instance.name
            hosts[hostname] = {
                "ansible_host": public_ip,
                "ansible_user": "ubuntu",
                "ansible_ssh_private_key_file": "~/.ssh/yandex_cloud_key",
                "ansible_python_interpreter": "/usr/bin/python3",
                "yc_instance_id": instance.id,
                "yc_zone": instance.zone_id,
                "yc_labels": dict(instance.labels),
            }
            webservers.append(hostname)

        return {
            "_meta": {"hostvars": hosts},
            "all": {"hosts": list(hosts.keys()), "vars": {}},
            "webservers": {"hosts": webservers},
        }

    except Exception as e:
        print(f"Error querying Yandex Cloud: {e}", file=sys.stderr)
        return {
            "_meta": {"hostvars": {}},
            "all": {"hosts": [], "vars": {}},
            "webservers": {"hosts": []},
        }


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(get_inventory(), indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        inventory = get_inventory()
        hostvars = inventory.get("_meta", {}).get("hostvars", {})
        host = sys.argv[2]
        print(json.dumps(hostvars.get(host, {}), indent=2))
    else:
        print(json.dumps(get_inventory(), indent=2))


if __name__ == "__main__":
    main()
