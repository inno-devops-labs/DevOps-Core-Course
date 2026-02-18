# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version**: 2.20.2 (control node: Arch Linux)
- **Target VM**: Ubuntu 24.04 LTS (running on VirtualBox, accessible via SSH on port 2222)
- **Project structure**: Role-based, following recommended Ansible practices.

```
ansible
├── ansible.cfg
├── docs
│   └── LAB05.md # this doc
├── inventory
│   ├── group_vars
│   │   └── all.yml # encrypted variables (Ansible vault)
│   └── hosts.ini # static inventory
├── playbooks
│   ├── deploy.yml # application deployment
│   └── provision.yml # system provisioning
└── roles
    ├── app_deploy # application deployment
    │   ├── defaults 
    │   │   └── main.yml 
    │   ├── handlers
    │   │   └── main.yml
    │   └── tasks
    │       └── main.yml
    ├── common # common system packages
    │   ├── defaults
    │   │   └── main.yml
    │   ├── handlers
    │   └── tasks
    │       └── main.yml
    └── docker # docker installation
        ├── defaults
        │   └── main.yml
        ├── handlers
        │   └── main.yml
        └── tasks
            └── main.yml
```

- **Why roles?** Roles enable modular, reusable, and maintainable automation. Each role focuses on a specific concern, making the playbooks clean and easy to extend.

## 2. Roles Documentation

### 2.1 `common` Role

**Purpose**: Install essential system packages and ensure the system is up‑to‑date.

**Variables** (in `defaults/main.yml`):
```yaml
common_packages:
  - python3-pip
  - curl
  - wget
  - git
  - vim
  - htop
  - net-tools
  - unzip
```

**Tasks**:
- Update APT cache (with `cache_valid_time=3600` to avoid unnecessary updates)
- Install the packages listed above.

### 2.2 `docker` Role

**Purpose**: Install Docker CE and its dependencies, start the Docker service, and add the remote user to the `docker` group.

**Variables** (`defaults/main.yml`):
```yaml
docker_user: "{{ ansible_user }}"
docker_packages:
  - docker-ce
  - docker-ce-cli
  - containerd.io
  - docker-buildx-plugin
  - docker-compose-plugin
```

**Handlers** (`handlers/main.yml`):
- `restart docker` – restarts the Docker daemon (used after configuration changes).

**Tasks**:
1. Remove any conflicting packages (like `docker.io`).
2. Install required system packages (`ca-certificates`, `curl`).
3. Create the keyrings directory.
4. Add Docker’s official GPG key.
5. Add the Docker APT repository (using `ansible_distribution_release` to get the Ubuntu codename).
6. Install Docker packages.
7. Ensure Docker is running and enabled.
8. Add the user to the `docker` group.
9. Install `python3-docker` via APT (required for Ansible Docker modules).

### 2.3 `app_deploy` Role

**Purpose**: Pull the Docker image from Docker Hub and run the container with the correct configuration.

**Variables** (`defaults/main.yml`):
```yaml
app_restart_policy: unless-stopped
app_env_vars: {}
```
Actual values (image name, tag, port) are taken from the encrypted `group_vars/all.yml`.

**Handlers** (`handlers/main.yml`):
- `restart app container` – restarts the application container (not used in current version but defined for future use).

**Tasks**:
1. **Login to Docker Hub** – uses credentials from vault (with `no_log: true` to hide secrets).
2. **Pull the Docker image** – pulls `s3rap1s/devops-info-service:latest`.
3. **Check if container is already running** – registers `container_info`.
4. **Stop and remove existing container** – if it exists.
5. **Run the container** – with the following parameters:
   - name: `devops-info-service`
   - image: `s3rap1s/devops-info-service:latest`
   - restart policy: `unless-stopped`
   - port mapping: `5000:5000`
6. **Wait for the application to be ready** – using `wait_for` on port 5000.
7. **Verify health endpoint** – using `uri` module to check `/health` returns 200 OK.
8. **Display health check result** – prints the JSON response.

## 3. Idempotency Demonstration

### First run of `provision.yml`

```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab04 ● ● λ ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass 

PLAY [Provision web servers with common tools and Docker] **********************************************************************************************************************************************************************************************************************

TASK [Gathering Facts] *********************************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [common : Install common essential packages] ******************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [docker : Remove conflicting packages] ************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *******************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] **************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker's official GPG key] **********************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [docker : Add Docker APT repository] **************************************************************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:39:11

37 - name: Add Docker APT repository
38   apt_repository:
39     repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker.asc...
             ^ column 11

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

changed: [devops-vm]

TASK [docker : Install Docker packages] ****************************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] ***************************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************************************************************************************************************************************************************************************************************
changed: [devops-vm]

PLAY RECAP *********************************************************************************************************************************************************************************************************************************************************************
devops-vm                  : ok=5   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

### Second run of `provision.yml`

```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab04 ● ● λ ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass

PLAY [Provision web servers with common tools and Docker] **********************************************************************************************************************************************************************************************************************

TASK [Gathering Facts] *********************************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Update apt cache] ***********************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [common : Install common essential packages] ******************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Remove conflicting packages] ************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install required system packages] *******************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Create keyrings directory] **************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker's official GPG key] **********************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add Docker APT repository] **************************************************************************************************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/s3rap1s/devops/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:39:11

37 - name: Add Docker APT repository
38   apt_repository:
39     repo: "deb [arch={{ ansible_architecture | replace('x86_64','amd64') }} signed-by=/etc/apt/keyrings/docker.asc...
             ^ column 11

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [devops-vm]

TASK [docker : Install Docker packages] ****************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Ensure Docker service is running and enabled] *******************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Add user to docker group] ***************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************************************************************************************************************************************************************************************************************
ok: [devops-vm]

PLAY RECAP *********************************************************************************************************************************************************************************************************************************************************************
devops-vm                  : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0  
```

**Analysis**:
- First run: many tasks reported **changed** because packages were installed, repositories added, etc.
- Second run: all tasks reported **ok** (green) because the system already matched the desired state.
- This **idempotency** proves that the roles are correctly written – they only make changes when necessary and do not break anything when run repeatedly.

## 4. Ansible Vault Usage

Sensitive information (Docker Hub credentials) is stored encrypted using Ansible Vault.

**Creation of vault file**:
```bash
ansible-vault create inventory/group_vars/all.yml
```
Vault password is stored in a local `.vault_pass` file (added to `.gitignore`). The vault file contains:
```yaml
dockerhub_username: "s3rap1s"
dockerhub_password: "dckr_pat_xxxxxx"   # nah uh
app_name: "devops-info-service"
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: "latest"
app_port: 5000
app_container_name: "{{ app_name }}"
```

**Usage in playbook**:
All tasks that use these variables refer to them normally. The vault password is supplied via the command line:
```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

**Why Ansible Vault matters**:
- Secrets are never exposed in plain text.
- The vault file can be safely committed to Git (it is encrypted).
- Access to secrets is controlled by the vault password, which is kept outside the repository.

## 5. Deployment Verification

### Playbook execution
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab04 ● ● λ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass   

PLAY [Deploy application] ******************************************************************************************************************************************************************************************************************************************************

TASK [Gathering Facts] *********************************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Log in to Docker Hub] ***************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Pull Docker image] ******************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Check if container is running] ******************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Stop and remove existing container if it exists] ************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [app_deploy : Run Docker container] ***************************************************************************************************************************************************************************************************************************************
changed: [devops-vm]

TASK [app_deploy : Wait for application to be ready] ***************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Verify health endpoint] *************************************************************************************************************************************************************************************************************************************
ok: [devops-vm]

TASK [app_deploy : Display health check result] ********************************************************************************************************************************************************************************************************************************
ok: [devops-vm] => {
    "msg": "Health check passed! Response: {'status': 'healthy', 'timestamp': '2026-02-25T13:03:39.898895+00:00', 'uptime_seconds': 5}"
}

PLAY RECAP *********************************************************************************************************************************************************************************************************************************************************************
devops-vm                  : ok=9    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```

### Manual checks
```bash
s3rap1s in ~/devops/DevOps-Core-Course/ansible on lab04 ● ● λ ssh devops@localhost -p 2222
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Feb 25 01:03:17 PM UTC 2026

  System load:             0.0
  Usage of /:              16.8% of 24.44GB
  Memory usage:            20%
  Swap usage:              0%
  Processes:               111
  Users logged in:         1
  IPv4 address for enp0s3: 10.0.2.15
  IPv6 address for enp0s3: fd17:625c:f037:2:a00:27ff:fe00:936e

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

20 updates can be applied immediately.
17 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


Last login: Wed Feb 25 13:03:39 2026 from 10.0.2.2
devops@devops:~$ docker ps
CONTAINER ID   IMAGE                                COMMAND           CREATED          STATUS          PORTS                    NAMES
9efe64c0a550   s3rap1s/devops-info-service:latest   "python app.py"   28 seconds ago   Up 27 seconds   0.0.0.0:5000->5000/tcp   devops-info-service
devops@devops:~$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-02-25T13:04:18.686599+00:00","uptime_seconds":44}
```

Everything works as expected – the application is running and healthy.

## 6. Key Decisions

### Why use roles instead of plain playbooks?
- **Reusability**: the same role can be applied to multiple hosts or projects.
- **Maintainability**: each role is isolated, making it easier to update or debug one part without affecting others.
- **Clarity**: the structure clearly separates concerns (system, Docker, application).

### How do roles improve reusability?
- Roles can be shared via Ansible Galaxy.
- Variables and defaults allow easy customisation without changing the role code.
- Handlers and files are bundled together, so the role is self-contained.

### What makes a task idempotent?
- Using state‑oriented modules (e.g., `apt: state=present`, `service: state=started`) instead of raw commands.
- Modules check the current state before applying changes and only act when necessary.
- For example, the Docker repository is added only once; subsequent runs see that it already exists.

### How do handlers improve efficiency?
- Handlers are triggered only when a task reports a change, and run once at the end of the play.
- This avoids unnecessary restarts (e.g., restarting Docker after every small change).

### Why is Ansible Vault necessary?
- To store secrets (passwords, tokens) securely in version control.
- Prevents accidental exposure of credentials.
- Enforces that only authorised users (with the vault password) can see the secrets.

## 7. Challenges (Optional)

- **HashiCorp repository error**: The target VM had a broken `hashicorp.list` file that caused `apt update` to fail. Solved by manually removing the file (`sudo rm /etc/apt/sources.list.d/hashicorp.list`).
- **Python external‑management error**: Ubuntu 24.04 blocks `pip install` system‑wide. Replaced `pip` installation of `docker` Python module with `apt install python3-docker`.
- **Vault variables not visible in roles**: Initially the variables from `group_vars/all.yml` were not loaded because the file was placed in the wrong directory. Moving it to `inventory/group_vars/all.yml` solved the issue.
- **Timeout on health check**: The `wait_for` task was delegated to `localhost` while the container runs inside the VM. Removing `delegate_to: localhost` fixed it.

## 8. Bonus Task – Dynamic Inventory (Theoretical)

If I had a cloud VM (e.g., on AWS or Yandex Cloud), I would implement dynamic inventory to avoid hardcoding IP addresses.

**Planned approach** (for AWS as an example):

1. Install the required collection:
   ```bash
   ansible-galaxy collection install amazon.aws
   ```

2. Create `inventory/aws_ec2.yml`:
   ```yaml
   plugin: amazon.aws.aws_ec2
   regions:
     - us-east-1
   filters:
     instance-state-name: running
     tag:Environment: dev
   keyed_groups:
     - key: tags.Role
       prefix: role
   hostnames:
     - public-ip-address
   compose:
     ansible_user: "'ubuntu'"
   ```

3. Use it with the existing playbooks:
   ```bash
   ansible-playbook -i inventory/aws_ec2.yml playbooks/provision.yml
   ```

**Benefits of dynamic inventory**:
- Automatically discovers new instances.
- Groups hosts by tags (e.g., `role_webserver`).
- No manual updates when IPs change.

**Why not implemented here**:
- I used a local VM for cost reasons and simplicity, so there is no cloud infrastructure to manage dynamically.
