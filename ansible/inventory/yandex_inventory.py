#!/usr/bin/env python3
"""
Dynamic inventory script for Yandex Cloud.
Queries the Yandex Compute API and returns running VMs as Ansible inventory.

Usage:
  ansible -i inventory/yandex_inventory.py all -m ping
  ansible-inventory -i inventory/yandex_inventory.py --graph
"""

import json
import os
import sys

import grpc
import yandexcloud
from yandex.cloud.compute.v1.instance_service_pb2 import ListInstancesRequest
from yandex.cloud.compute.v1.instance_service_pb2_grpc import InstanceServiceStub

FOLDER_ID = "b1ga4ttr9f92otmhh4cc"
SERVICE_ACCOUNT_KEY_FILE = "/home/blxxdclxud/yc-key.json"
SSH_USER = "ubuntu"
SSH_KEY = "~/.ssh/id_ed25519"


def get_instances():
    with open(SERVICE_ACCOUNT_KEY_FILE) as f:
        sa_key = json.load(f)

    sdk = yandexcloud.SDK(service_account_key=sa_key)
    instance_service = sdk.client(InstanceServiceStub)

    response = instance_service.List(ListInstancesRequest(folder_id=FOLDER_ID))
    return [i for i in response.instances if i.status == 2]  # 2 = RUNNING


def build_inventory(instances):
    hostvars = {}
    webservers = []

    for instance in instances:
        name = instance.name
        public_ip = None

        for iface in instance.network_interfaces:
            if iface.primary_v4_address.one_to_one_nat.address:
                public_ip = iface.primary_v4_address.one_to_one_nat.address
                break

        if not public_ip:
            continue

        hostvars[name] = {
            "ansible_host": public_ip,
            "ansible_user": SSH_USER,
            "ansible_ssh_private_key_file": SSH_KEY,
            "yc_labels": dict(instance.labels),
        }

        if instance.labels.get("project", "") == "devops-lab04":
            webservers.append(name)

    return {
        "all": {
            "hosts": list(hostvars.keys()),
        },
        "webservers": {
            "hosts": webservers,
        },
        "_meta": {
            "hostvars": hostvars,
        },
    }


if __name__ == "__main__":
    if "--list" in sys.argv:
        instances = get_instances()
        inventory = build_inventory(instances)
        print(json.dumps(inventory, indent=2))
    elif "--host" in sys.argv:
        print(json.dumps({}))
    else:
        print(json.dumps({}))
