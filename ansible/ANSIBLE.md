```bash

PLAY [Deploy Docker on cloud VM] *********************************************************

TASK [Gathering Facts] *******************************************************************
[WARNING]: Platform linux on host my_cloud_vm is using the discovered Python interpreter
at /usr/bin/python3.12, but future installation of another Python interpreter could
change the meaning of that path. See https://docs.ansible.com/ansible-
core/2.18/reference_appendices/interpreter_discovery.html for more information.
ok: [my_cloud_vm]

TASK [docker : include_tasks] ************************************************************
included: /home/ezzy/study/S25-core-course-labs/ansible/roles/docker/tasks/install_docker.yml for my_cloud_vm

TASK [docker : Install required packages] ************************************************
ok: [my_cloud_vm]

TASK [docker : Add Docker GPG key] *******************************************************
ok: [my_cloud_vm]

TASK [docker : Add Docker repository] ****************************************************
ok: [my_cloud_vm]

TASK [docker : Update apt cache again] ***************************************************
changed: [my_cloud_vm]

TASK [docker : Install Docker CE] ********************************************************
ok: [my_cloud_vm]

TASK [docker : include_tasks] ************************************************************
included: /home/ezzy/study/S25-core-course-labs/ansible/roles/docker/tasks/install_compose.yml for my_cloud_vm

TASK [docker : Download Docker Compose binary] *******************************************
changed: [my_cloud_vm]

TASK [docker : Enable and start Docker] **************************************************
ok: [my_cloud_vm]

TASK [docker : Add user to docker group] *************************************************
changed: [my_cloud_vm]

PLAY RECAP *******************************************************************************
my_cloud_vm                : ok=11   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```



## Playbook output:
```bash
{
    "_meta": {
        "hostvars": {
            "my_cloud_vm": {
                "ansible_host": "51.250.12.24",
                "ansible_ssh_private_key_file": "/home/ezzy/.ssh/id_ed25519",
                "ansible_user": "ezzy"
            }
        }
    },
    "all": {
        "children": [
            "ungrouped"
        ]
    },
    "ungrouped": {
        "hosts": [
            "my_cloud_vm"
        ]
    }
}
```


```bash
@all:
  |--@ungrouped:
  |  |--my_cloud_vm
```

