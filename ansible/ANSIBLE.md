# Ansible Deployment Documentation

## Overview

This document outlines the configuration and deployment process for the custom Docker role. The role installs Docker and Docker Compose, ensures the Docker service is enabled at boot, adds the current user to the Docker group so Docker commands can be run without sudo, and configures a secure Docker daemon.

## Project Structure

```sh
     .
     |-- README.md
     |-- ansible
     |   |-- inventory
     |   |   |-- yandex_cloud.yml
     |   |    
     |   |-- playbooks
     |   |   -- dev
     |   |       -- main.yaml
     |   |-- roles
     |   |   |-- docker
     |   |   |   |-- defaults
     |   |   |   |   `-- main.yml
     |   |   |   |-- handlers
     |   |   |   |   `-- main.yml
     |   |   |   |-- tasks
     |   |   |   |   |-- docker_users.yml
     |   |   |   |   |-- install_compose.yml
     |   |   |   |   |-- install_docker.yml
     |   |   |   |   |-- main.yml
     |   |   |   |   |-- manager.yml
     |   |   |   |   |-- secure_docker.yml
     |   |   |   |   `-- setup_debian.yml  
     |   |   |   `-- README.md
     |   |   `-- web_app
     |   |       |-- defaults
     |   |       |   `-- main.yml
     |   |       |-- handlers
     |   |       |   `-- main.yml
     |   |       |-- meta
     |   |       |   `-- main.yml
     |   |       |-- tasks
     |   |       |   `-- main.yml
     |   |       `-- templates
     |   |           `-- docker-compose.yml.j2
     |   `-- ansible.cfg
     |-- app_python
     |-- app_typescript
     `-- terraform
```

## Inventory Details

- **Inventory File:** `ansible/inventory/yandex_cloud.yml`
- **Example Command to List Inventory:**

  ```bash
  ansible-inventory -i inventory/yandex_cloud.yml --list
  ```
- Output:
  
  ```
  kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-inventory -i inventory/yandex_cloud.yml --list 
     {
    "_meta": {
        "hostvars": {
            "yandex_vm": {
                "ansible_become": true,
                "ansible_host": "93.77.188.83",
                "ansible_python_interpreter": "/usr/bin/python3",
                "ansible_ssh_private_key_file": "~/.ssh/id_rsa",
                "ansible_user": "ubuntu"
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
              "yandex_vm"
          ]
      }
  } ```

- **Graphical Representation of Inventory:**
  ```bash
  ansible-inventory -i inventory/yandex_cloud.yml --graph 
```

- Output:
  ```
     kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-inventory -i inventory/yandex_cloud.yml --graph 
    
    @all:
      |--@ungrouped:
      |  |--yandex_vm  ```

  
## Playbook Execution

### Dry Run (Check Mode)

Before applying changes, perform a dry run to preview potential modifications:

```bash
ansible-playbook playbooks/dev/main.yaml --check --diff
```

**Output**:
```
kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-playbook playbooks/dev/main.yaml --diff --check

PLAY [Setup Docker] **************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Apt update] *******************************************************************************************************************************
changed: [yandex_vm]

TASK [docker : Remove old Docker versions] ***************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install required system packages] *********************************************************************************************************
ok: [yandex_vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Dearmor Docker GPG key] *******************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Set correct permissions on GPG key] *******************************************************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker repository] ********************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Ensure Docker service is enabled and started] *********************************************************************************************
ok: [yandex_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************
ok: [yandex_vm] => (item=docker)

TASK [docker : Enable and start Docker service] **********************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker Compose plugin] ************************************************************************************************************
ok: [yandex_vm]

PLAY RECAP ***********************************************************************************************************************************************
yandex_vm                  : ok=14   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
## Actual Deployment
To deploy the Docker role, run:
```bash
ansible-playbook playbooks/dev/main.yaml --check
```

**Output**:
```
kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-playbook playbooks/dev/main.yaml --diff

PLAY [Setup Docker] **************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Apt update] *******************************************************************************************************************************
changed: [yandex_vm]

TASK [docker : Remove old Docker versions] ***************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install required system packages] *********************************************************************************************************
ok: [yandex_vm]

TASK [docker : Create keyrings directory] ****************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Dearmor Docker GPG key] *******************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Set correct permissions on GPG key] *******************************************************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker repository] ********************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker packages] ******************************************************************************************************************
ok: [yandex_vm]

TASK [docker : Ensure Docker service is enabled and started] *********************************************************************************************
ok: [yandex_vm]

TASK [docker : Add users to docker group] ****************************************************************************************************************
ok: [yandex_vm] => (item=docker)

TASK [docker : Enable and start Docker service] **********************************************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker Compose plugin] ************************************************************************************************************
ok: [yandex_vm]

PLAY RECAP ***********************************************************************************************************************************************
yandex_vm                  : ok=14   changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
