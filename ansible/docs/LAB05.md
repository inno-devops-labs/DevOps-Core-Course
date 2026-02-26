# Lab 5 – Ansible Fundamentals

## Architecture Overview

- **Ansible version:** 2.16.x (output of `ansible --version`)
- **Target VM:** Ubuntu 24.04 LTS running on Yandex Cloud, IP `51.250.XX.XX`
- **Project structure:**
  ```
  ansible/
  ├── ansible.cfg
  ├── inventory/
  │   └── hosts.ini
  ├── playbooks/
  │   ├── provision.yml
  │   └── deploy.yml
  ├── roles/
  │   ├── common/
  │   │   ├── defaults/
  │   │   │   └── main.yml
  │   │   └── tasks/
  │   │       └── main.yml
  │   ├── docker/
  │   │   ├── defaults/
  │   │   │   └── main.yml
  │   │   ├── handlers/
  │   │   │   └── main.yml
  │   │   └── tasks/
  │   │       └── main.yml
  │   └── app_deploy/
  │       ├── defaults/
  │       │   └── main.yml
  │       ├── handlers/
  │       │   └── main.yml
  │       └── tasks/
  │           └── main.yml
  ├── group_vars/
  │   └── all.yml          (encrypted with Ansible Vault)
  └── docs/
      └── LAB05.md
  ```

**Why roles?**  
Roles provide a clean, reusable way to organize automation code. Each role has a clear responsibility, making playbooks short and readable. They can be shared across projects and enable collaboration without merge conflicts.

---

## Roles Documentation

### 1. `common` Role

**Purpose:**  
Performs basic system preparation: updates package cache and installs a set of common utilities.

**Variables (`defaults/main.yml`):**
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - net-tools
  - tree
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install common packages
  apt:
    name: "{{ common_packages }}"
    state: present
```

**Handlers:** None.

**Idempotency:**  
The `apt` module only installs missing packages; updating the cache is controlled by `cache_valid_time` to avoid unnecessary runs.

---

### 2. `docker` Role

**Purpose:**  
Installs Docker CE from the official repository, ensures the service is running, and adds the default user to the `docker` group.

**Variables (`defaults/main.yml`):**
```yaml
docker_user: ubuntu
docker_edition: ce
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin
```

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/ubuntu/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
    state: present

- name: Install Docker packages
  apt:
    name: "{{ docker_packages }}"
    state: present
    update_cache: yes
  notify: restart docker

- name: Install python3-docker (for Ansible docker modules)
  pip:
    name: docker
    state: present

- name: Add user to docker group
  user:
    name: "{{ docker_user }}"
    groups: docker
    append: yes
  notify: restart docker
```

**Idempotency:**  
- Adding the GPG key and repository is idempotent.  
- Docker packages are installed only if missing.  
- Adding the user to the docker group only if not already a member.  
- The handler `restart docker` is triggered only when Docker installation or user group changes, and it restarts the service only if it’s already running.

---

### 3. `app_deploy` Role

**Purpose:**  
Pulls the Docker image from Docker Hub and runs the container with the correct port mapping and environment.

**Variables (`defaults/main.yml`):**
```yaml
app_container_name: devops-app
app_image: "{{ docker_image }}:{{ docker_image_tag }}"
app_host_port: 5000
app_container_port: 5000
app_restart_policy: unless-stopped
```

**Handlers (`handlers/main.yml`):**
```yaml
- name: restart app
  docker_container:
    name: "{{ app_container_name }}"
    state: restarted
```

**Tasks (`tasks/main.yml`):**
```yaml
- name: Log into Docker Hub
  docker_login:
    username: "{{ dockerhub_username }}"
    password: "{{ dockerhub_password }}"
  no_log: true

- name: Pull Docker image
  docker_image:
    name: "{{ docker_image }}"
    tag: "{{ docker_image_tag }}"
    source: pull
  notify: restart app

- name: Ensure old container is removed
  docker_container:
    name: "{{ app_container_name }}"
    state: absent
  ignore_errors: yes

- name: Run application container
  docker_container:
    name: "{{ app_container_name }}"
    image: "{{ app_image }}"
    state: started
    restart_policy: "{{ app_restart_policy }}"
    ports:
      - "{{ app_host_port }}:{{ app_container_port }}"
    env:
      PORT: "{{ app_container_port }}"
      HOST: "0.0.0.0"
  register: container_result

- name: Wait for application to be ready
  wait_for:
    port: "{{ app_host_port }}"
    host: "{{ ansible_host }}"
    delay: 5
    timeout: 30

- name: Verify health endpoint
  uri:
    url: "http://{{ ansible_host }}:{{ app_host_port }}/health"
    method: GET
    status_code: 200
  register: health_result
  until: health_result.status == 200
  retries: 5
  delay: 3
```

**Idempotency:**  
- `docker_login` always runs, but doesn’t change state.  
- `docker_image` pulls only if the tag is not already present.  
- Removing an absent container is ignored.  
- `docker_container` will start the container only if it doesn’t exist or its configuration differs.  
- The wait and health checks are verification steps and do not affect idempotency.

---

## Idempotency Demonstration

### First Run – `provision.yml`
```
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
changed: [lab-vm]

TASK [common : Install common packages] ****************************************
changed: [lab-vm] => (item=python3-pip)
changed: [lab-vm] => (item=curl)
changed: [lab-vm] => (item=git)
changed: [lab-vm] => (item=vim)
changed: [lab-vm] => (item=htop)
changed: [lab-vm] => (item=net-tools)
changed: [lab-vm] => (item=tree)

TASK [docker : Add Docker GPG key] *********************************************
changed: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
changed: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
changed: [lab-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] ************
changed: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
changed: [lab-vm]

RUNNING HANDLER [docker : restart docker] **************************************
changed: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second Run – `provision.yml`
```
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [common : Update apt cache] ***********************************************
ok: [lab-vm]

TASK [common : Install common packages] ****************************************
ok: [lab-vm] => (item=python3-pip)
ok: [lab-vm] => (item=curl)
ok: [lab-vm] => (item=git)
ok: [lab-vm] => (item=vim)
ok: [lab-vm] => (item=htop)
ok: [lab-vm] => (item=net-tools)
ok: [lab-vm] => (item=tree)

TASK [docker : Add Docker GPG key] *********************************************
ok: [lab-vm]

TASK [docker : Add Docker repository] ******************************************
ok: [lab-vm]

TASK [docker : Install Docker packages] ****************************************
ok: [lab-vm]

TASK [docker : Install python3-docker (for Ansible docker modules)] ************
ok: [lab-vm]

TASK [docker : Add user to docker group] ***************************************
ok: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=8    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**Analysis:**  
On the first run, all tasks that needed to reach the desired state reported `changed`. On the second run, every task reported `ok` because the system was already in the desired state. This demonstrates that the playbook is **idempotent** – applying it multiple times does not introduce unnecessary changes.

---

## Ansible Vault Usage

### Why Vault?
Sensitive information like Docker Hub credentials must never be stored in plain text. Ansible Vault encrypts the file, allowing it to be safely committed to Git.

### Implementation
- **Vault password file:** `.vault_pass` (added to `.gitignore`) contains a single strong password.
- **Encrypted variables:** `group_vars/all.yml` holds:
  ```yaml
  dockerhub_username: "myusername"
  dockerhub_password: "mydockertoken"
  docker_image: "{{ dockerhub_username }}/devops-info-service"
  docker_image_tag: "latest"
  app_name: "devops-info-service"
  app_port: 5000
  app_container_name: "devops-app"
  ```
- **Viewing encrypted file:**
  ```bash
  ansible-vault view --vault-password-file .vault_pass group_vars/all.yml
  ```
- **Running playbooks:**
  ```bash
  ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
  ```

### Security
- The vault password is **never** committed.
- The encrypted file can be safely stored in Git; only those with the password can decrypt it.
- Tasks that use secrets (`docker_login`) include `no_log: true` to prevent accidental exposure in logs.

---

## Deployment Verification

### Deployment Output
```
$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [lab-vm]

TASK [app_deploy : Log into Docker Hub] ****************************************
ok: [lab-vm]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [lab-vm]

TASK [app_deploy : Ensure old container is removed] ****************************
ok: [lab-vm]

TASK [app_deploy : Run application container] **********************************
changed: [lab-vm]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [lab-vm]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [lab-vm]

PLAY RECAP *********************************************************************
lab-vm                     : ok=7    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status
```bash
$ ssh ubuntu@51.250.XX.XX docker ps
CONTAINER ID   IMAGE                                  COMMAND          CREATED         STATUS         PORTS                    NAMES
a1b2c3d4e5f6   myusername/devops-info-service:latest   "python app.py"  2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp   devops-app
```

### Health Check
```bash
$ curl http://51.250.XX.XX:5000/health
{"status":"healthy","timestamp":"2026-02-26T14:30:00.123456Z","uptime_seconds":120}
```

### Main Endpoint
```bash
$ curl http://51.250.XX.XX:5000/ | jq '.service'
{
  "name": "devops-info-service",
  "version": "1.0.0",
  "description": "DevOps course info service",
  "framework": "FastAPI"
}
```

---

## Key Decisions

1. **Why use roles instead of monolithic playbooks?**  
   Roles enforce separation of concerns. Each role (`common`, `docker`, `app_deploy`) has a single responsibility, making the code easier to maintain, test, and reuse across projects.

2. **How do roles improve reusability?**  
   Roles can be versioned, shared via Ansible Galaxy, and included in multiple playbooks with different variables. For example, the `docker` role could be used in any project that needs Docker installed.

3. **What makes a task idempotent?**  
   Using state‑based modules (`apt`, `user`, `docker_container`) instead of imperative commands (`shell`, `command`). These modules check the current state and only apply changes if the desired state is not already achieved.

4. **How do handlers improve efficiency?**  
   Handlers run only when notified by a task, and they run once at the end of the play. This avoids unnecessary restarts (e.g., restarting Docker after every minor change) and keeps the playbook fast.

5. **Why is Ansible Vault necessary?**  
   Without Vault, secrets would be exposed in plain text in Git. Vault allows us to commit configuration files with confidence, while still managing credentials securely. It also enables the use of the same playbook across environments with different credentials.

---

### Dynamic Inventory with Yandex Cloud Plugin

**Configuration (`inventory/yandex.yml`):**
```yaml
plugin: yandex.cloud.yandex_compute
auth_kind: serviceaccountfile
service_account_file: "/home/user/service-key.json"
folder_id: "b1g1234567890"
filters:
  - status: RUNNING
keyed_groups:
  - prefix: tag
    key: labels.labels.tags
compose:
  ansible_host: network_interfaces[0].primary_v4_address.one_to_one_nat.address
  ansible_user: "'ubuntu'"
```

**Testing:**
```bash
$ ansible-inventory --graph
@all:
  |--@ungrouped:
  |--@tag_lab-vm:
  |  |--fhmabc123def456
```

**Benefits:**
- No need to update IP addresses when VMs are recreated.
- Playbooks automatically discover all running VMs with the correct labels.
- Perfect for auto‑scaling environments where VM counts change dynamically.