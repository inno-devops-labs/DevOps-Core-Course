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


## Web app deployment

### Dry Run (Check Mode)

Before applying changes, perform a dry run to preview potential modifications:


```bash
ansible-playbook playbooks/dev/main.yaml --check --diff
```

#### Commands output:
```
kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-playbook playbooks/dev/web_app/main.yaml --check --
diff

/usr/lib/python3/dist-packages/paramiko/pkey.py:82: CryptographyDeprecationWarning: TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 48.0.0.
  "cipher": algorithms.TripleDES,
/usr/lib/python3/dist-packages/paramiko/transport.py:237: CryptographyDeprecationWarning: Blowfish has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.Blowfish and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 45.0.0.
  "class": algorithms.Blowfish,
/usr/lib/python3/dist-packages/paramiko/transport.py:261: CryptographyDeprecationWarning: TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 48.0.0.
  "class": algorithms.TripleDES,

PLAY [Setup Docker] **************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************
ok: [yandex_vm]

TASK [docker : Apt update] *******************************************************************************************
changed: [yandex_vm]

TASK [docker : Remove old Docker versions] ***************************************************************************
ok: [yandex_vm]

TASK [docker : Install required system packages] *********************************************************************
ok: [yandex_vm]

TASK [docker : Create keyrings directory] ****************************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker GPG key] ***********************************************************************************
changed: [yandex_vm]

TASK [docker : Dearmor Docker GPG key] *******************************************************************************
ok: [yandex_vm]

TASK [docker : Set correct permissions on GPG key] *******************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker repository] ********************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker packages] ******************************************************************************
ok: [yandex_vm]

TASK [docker : Ensure Docker service is enabled and started] *********************************************************
ok: [yandex_vm]

TASK [docker : Add users to docker group] ****************************************************************************
ok: [yandex_vm] => (item=docker)

TASK [docker : Enable and start Docker service] **********************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker Compose plugin] ************************************************************************
ok: [yandex_vm]

PLAY RECAP ***********************************************************************************************************
yandex_vm                  : ok=14   changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

### Commands output:

```bash
ansible-playbook playbooks/dev/main.yaml 
```

```
kokai@kokai:~/Desktop/S25-core-course-labs/ansible$ ansible-playbook playbooks/dev/web_app/main.yml 
[DEPRECATION WARNING]: Specifying a list of dictionaries for vars is deprecated in favor of specifying a 
dictionary. This feature will be removed in version 2.18. Deprecation warnings can be disabled by setting 
deprecation_warnings=False in ansible.cfg.
[WARNING]: Collection community.docker does not support Ansible version 2.15.13

PLAY [Deploy python application] *****************************************************************************

TASK [Gathering Facts] ***************************************************************************************
ok: [yandex_vm]

TASK [docker : Apt update] ***********************************************************************************
changed: [yandex_vm]

TASK [docker : Remove old Docker versions] *******************************************************************
ok: [yandex_vm]

TASK [docker : Install required system packages] *************************************************************
ok: [yandex_vm]

TASK [docker : Create keyrings directory] ********************************************************************
ok: [yandex_vm]

TASK [docker : Add Docker GPG key] ***************************************************************************
ok: [yandex_vm]

TASK [docker : Dearmor Docker GPG key] ***********************************************************************
ok: [yandex_vm]

TASK [docker : Set correct permissions on GPG key] ***********************************************************
ok: [yandex_vm]

TASK [docker : Add Docker repository] ************************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker packages] **********************************************************************
ok: [yandex_vm]

TASK [docker : Ensure Docker service is enabled and started] *************************************************
ok: [yandex_vm]

TASK [docker : Add users to docker group] ********************************************************************
ok: [yandex_vm] => (item=docker)

TASK [docker : Enable and start Docker service] **************************************************************
ok: [yandex_vm]

TASK [docker : Install Docker Compose plugin] ****************************************************************
ok: [yandex_vm]

TASK [web_app : create new directory] ************************************************************************
ok: [yandex_vm]

TASK [web_app : Enable docker] *******************************************************************************
ok: [yandex_vm]

TASK [web_app : Pull docker image] ***************************************************************************
changed: [yandex_vm]

TASK [web_app : Copy docker compose file] ********************************************************************
changed: [yandex_vm]

TASK [web_app : Run docker container] ************************************************************************
[WARNING]: Docker compose: unknown None: /home/ubuntu/web_app/docker-compose.yml: the attribute `version` is
obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [yandex_vm]

TASK [web_app : include_tasks] *******************************************************************************
included: /home/ahmad/Desktop/S25-core-course-labs/ansible/roles/web_app/tasks/0-wipe.yml for yandex_vm

TASK [web_app : Remove the docker container] *****************************************************************
changed: [yandex_vm]

TASK [web_app : Clean directories] ***************************************************************************
changed: [yandex_vm]

PLAY RECAP ***************************************************************************************************
yandex_vm                  : ok=22   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
