# Lab 5 - Ansible Fundamentals

## 1. Architecture Overview

### Ansible version used

After installing ansible using `apt install ansible` on Ubuntu 24.04,
the following version was installed: `ansible [core 2.16.3]`

### Target VM OS and version

VM is running on QEMU/KVM. VM is running Ubuntu 24.04

Output of `cat /etc/os-release`

```
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION="24.04.4 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
...
```

### Role structure diagram or explanation

Project uses the standard Ansible directory layout with `playbooks/` directory containing the playbook files, and `roles/` directory containing reusable rolws. Each role has its own directory with `tasks/`, `defaults/`, `handlers/` folders.

### Why roles instead of monolithic playbooks?
A single playbook is hard to maintain and reuse. Splitting the playbook into roles allows for more code reuse and easier maintainability.

## 2. Roles Documentation

### common

#### Purpose

Make sure the system has an updated apt cache and install reqiored package: `python3-pip` and `curl`.

#### Variables

`common_packages` (default `['python3-pip','curl']`).

#### Handlers

none defined in this role.

#### Dependencies

none. It can run on a raw OS image.

### docker

#### Purpose

Configure the official Docker apt repository, install docker and related packages, ensure the `docker` service is running and add the specified user to the docker group. It also installs the `python3-docker` package which is useful for Ansible Docker modules.

#### Variables

`docker_user` (default `cirno`), `docker_group` (`docker`), `python3_docker_package` (`python3-docker`).

#### Handlers

none. Service start/enable is done directly in tasks.

#### Dependencies

none. Although it is typically invoked after `common` in the playbook.

### app_deploy

#### Purpose

Log in to Docker Hub, pull the application image, stop and remove any existing container, start a new container and verify it is healthy.

#### Variables

defaults include `app_name`, `app_port`, `app_container_name` and `container_restart_policy`. Additional required variables such as `dockerhub_username`, `dockerhub_password`, `docker_image` and `docker_image_tag` are supplied via encrypted group vars.

#### Handlers

none. The tasks manage containers directly.

#### Dependencies

none. It assumes Docker is already installed and running.

## 3. Idempotency Demonstration

### Terminal output from FIRST provision.yml run

```
PLAY [Provision web servers] *****************************************************************

TASK [Gathering Facts] ***********************************************************************
ok: [devops-lab4-vm]

TASK [common : Update apt cache] *************************************************************
ok: [devops-lab4-vm]

TASK [common : Install common packages] ******************************************************
ok: [devops-lab4-vm]

TASK [docker : Add Docker GPG key] ***********************************************************
ok: [devops-lab4-vm]

TASK [docker : Add Docker repository] ********************************************************
ok: [devops-lab4-vm]

TASK [docker : Update apt cache] *************************************************************
ok: [devops-lab4-vm]

TASK [docker : Install Docker packages] ******************************************************
ok: [devops-lab4-vm]

TASK [docker : Check Docker service running] *************************************************
ok: [devops-lab4-vm]

TASK [docker : Add user to docker group] *****************************************************
ok: [devops-lab4-vm]

TASK [docker : Install python3-docker package] ***********************************************
ok: [devops-lab4-vm]

PLAY RECAP ***********************************************************************************
devops-lab4-vm             : ok=10   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Terminal output from SECOND provision.yml run

```
PLAY [Provision web servers] *****************************************************************

TASK [Gathering Facts] ***********************************************************************
ok: [devops-lab4-vm]

TASK [common : Update apt cache] *************************************************************
ok: [devops-lab4-vm]

TASK [common : Install common packages] ******************************************************
ok: [devops-lab4-vm]

TASK [docker : Add Docker GPG key] ***********************************************************
ok: [devops-lab4-vm]

TASK [docker : Add Docker repository] ********************************************************
ok: [devops-lab4-vm]

TASK [docker : Update apt cache] *************************************************************
ok: [devops-lab4-vm]

TASK [docker : Install Docker packages] ******************************************************
ok: [devops-lab4-vm]

TASK [docker : Check Docker service running] *************************************************
ok: [devops-lab4-vm]

TASK [docker : Add user to docker group] *****************************************************
ok: [devops-lab4-vm]

TASK [docker : Install python3-docker package] ***********************************************
ok: [devops-lab4-vm]

PLAY RECAP ***********************************************************************************
devops-lab4-vm             : ok=10   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis: What changed first time? What didn't change second time?

I had lost the original `provision.yml` run, so this is a rerun, so the output shows `ok` for every task and the recap reported `changed=0`. This already shows that actions are idempotent.

When the same playbook was run a second time nothing was changed. Every task again shows `ok` and the shows `changed=0`. The packages, repository entries and user group membership were already in the required state, so Ansible skipped operations that are already done.

### Explanation: What makes your roles idempotent?

Idempotency is achieved by using module parameters: `state: present`, `update_cache: yes`. so that each task describes the required end-state rather than performing an unconditional change. The modules themselves are written to check the current state before acting. In addition, the roles avoid running shell commands.

## 4. Ansible Vault Usage

### How you store credentials securely

The credentials are stored in the `inventory/group_vars/all.yml` file (the lab tasks suggest storing it in `group_vars/all.yml`, outside of `inventory/` but I had lots of issues with this approach and switched to storing the group vars inside the `inventory/` directory).

### Vault password management strategy

Password is loaded using the `--ask-vault-password` flag of the `ansible-playbook` command.

### Example of encrypted file (show it's encrypted!)

The file starts with AES256 and contains a string of numbers that represent encrypted file contents.

```
$ANSIBLE_VAULT;1.1;AES256
303733626265626138346437633...
```

### Why Ansible Vault is important

Ansible vault allows to distribute all the secrets needed for the service in the version control in a secure encrypted form.

## 5. Deployment Verification

### Terminal output from deploy.yml run

```
PLAY [Deploy application] ********************************************************************

TASK [Gathering Facts] ***********************************************************************
ok: [devops-lab4-vm]

TASK [app_deploy : Docker Login] *************************************************************
ok: [devops-lab4-vm]

TASK [app_deploy : Pull Docker image] ********************************************************
ok: [devops-lab4-vm]

TASK [app_deploy : Stop container] ***********************************************************
changed: [devops-lab4-vm]

TASK [app_deploy : Remove container] *********************************************************
changed: [devops-lab4-vm]

TASK [app_deploy : Run container] ************************************************************
changed: [devops-lab4-vm]

TASK [app_deploy : Wait for container] *******************************************************
ok: [devops-lab4-vm]

TASK [app_deploy : Check health] *************************************************************
ok: [devops-lab4-vm]

PLAY RECAP ***********************************************************************************
devops-lab4-vm             : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container status

Running `docker ps` in the vm:

```
cirno@devops-lab4-vm:~$ docker ps
CONTAINER ID   IMAGE                                     COMMAND           CREATED         STATUS         PORTS                    NAMES
bb033d424504   iucapstonead/devops-info-service:latest   "python app.py"   6 minutes ago   Up 6 minutes   0.0.0.0:5000->5000/tcp   devops-app
```

### Health check of the application running inside the vm

```
cirno@t14-devops:~/Documents/DevOps-Core-Course/ansible$ curl 192.168.122.243:5000/health
{"status":"healthy","timestamp":"2026-02-26T17:10:11.970856+00:00","uptime_seconds":475}
```

## 6. Key Decisions

### Why use roles instead of plain playbooks?

Playbooks are hard to maintain and modify. Roles can be easily reused and allow to share configuration across project.

### How do roles improve reusability?

Each role is self-contained, therefore they can be copied into a different repository, without having to extract the relevant tasks from a monolithic file. Parameterizing the defaults means the same role can configure multiple hosts in slightly different ways.

### What makes a task idempotent?

A task is idempotent when running it once has the same effect as running it multiple times. The second and subsequent runs detect that the resource already exists and do nothing. In Ansible this is done using arguments `state: present`, `enabled: yes`. And not using direct shell commands. The modules check the system before making changes and report `changed` only if there was a change.

### How do handlers improve efficiency?

Handlers are triggered only when a task reports `changed`, which allows to ensure that actions run exactly once even if multiple tasks signal a change.

### Why is Ansible Vault necessary?

Credentials such as Docker Hub passwords or API keys must not be stored in plaintext in version control. Vault encrypts these variables so the repository can be shared or pushed to Git without leaking secrets.
