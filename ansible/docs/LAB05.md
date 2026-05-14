# Lab 05 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** 2.20.5 (core)
- **Target VM:** Ubuntu 24.04 LTS (93.77.181.6, from Lab 4 Pulumi)
- **Control node:** macOS (local machine)

### Role Structure:
ansible/
├── inventory/hosts.ini        # Static inventory with VM IP
├── roles/
│   ├── common/                # System packages
│   ├── docker/                # Docker installation
│   └── app_deploy/            # Application deployment
├── playbooks/
│   ├── provision.yml          # Runs common + docker roles
│   └── deploy.yml             # Runs app_deploy role
├── group_vars/all.yml         # Encrypted credentials (Vault)
└── ansible.cfg                # Ansible configuration

**Why roles instead of monolithic playbooks?**
Roles separate concerns — each role does one thing. This makes code reusable, testable, and easy to maintain. A monolithic playbook becomes hard to read and impossible to reuse across projects.

---

## 2. Roles Documentation

### common role
- **Purpose:** Updates apt cache and installs essential system packages
- **Variables:** `common_packages` — list of packages to install (python3-pip, curl, git, vim, htop, etc.)
- **Handlers:** None
- **Dependencies:** None

### docker role
- **Purpose:** Installs Docker CE on the target VM, ensures service is running, adds user to docker group
- **Variables:** `docker_user` — user to add to docker group (default: ubuntu)
- **Handlers:** `restart docker` — restarts Docker service when triggered by package installation
- **Dependencies:** common (apt cache must be updated)

### app_deploy role
- **Purpose:** Logs into Docker Hub, pulls image, stops old container, runs new container, verifies health
- **Variables:**
  - `app_port: 5000`
  - `app_restart_policy: unless-stopped`
  - `dockerhub_username, dockerhub_password` — from Vault
  - `docker_image, docker_image_tag, app_container_name` — from Vault
- **Handlers:** `restart app` — restarts application container
- **Dependencies:** docker role must be applied first

---

## 3. Idempotency Demonstration

### First run output:
TASK [common : Update apt cache] .............. changed
TASK [common : Install common packages] ....... changed
TASK [docker : Add Docker GPG key] ............ changed
TASK [docker : Add Docker repository] ......... changed
TASK [docker : Install Docker packages] ....... changed
TASK [docker : Add user to docker group] ...... changed
TASK [docker : Install python3-docker] ........ changed
RUNNING HANDLER [docker : restart docker] ..... changed
PLAY RECAP
lab04-vm: ok=12  changed=8  unreachable=0  failed=0

### Second run output:
TASK [common : Update apt cache] .............. ok
TASK [common : Install common packages] ....... ok
TASK [docker : Add Docker GPG key] ............ ok
TASK [docker : Add Docker repository] ......... ok
TASK [docker : Install Docker packages] ....... ok
TASK [docker : Add user to docker group] ...... ok
TASK [docker : Install python3-docker] ........ ok
PLAY RECAP
lab04-vm: ok=11  changed=0  unreachable=0  failed=0

**Analysis:** First run made 8 changes — installed packages, added GPG key, added repository, added user to group, restarted Docker. Second run showed 0 changes because all desired states were already achieved. Tasks are idempotent because Ansible modules (apt, apt_key, apt_repository, user, service) check current state before acting.

---

## 4. Ansible Vault Usage

Credentials stored in `group_vars/all.yml`, encrypted with Ansible Vault:
$ANSIBLE_VAULT;1.1;AES256
62633836313162393136646664616231633635383338...

- Vault password stored in `.vault_pass` (added to .gitignore)
- File encrypted with `ansible-vault encrypt`
- Viewed with `ansible-vault view group_vars/all.yml`
- Edited with `ansible-vault edit group_vars/all.yml`

**Why Ansible Vault is important:** Credentials must never be stored in plaintext in version control. Vault encrypts secrets so they can be safely committed to Git while remaining inaccessible without the vault password.

---

## 5. Deployment Verification

### deploy.yml run output:
TASK [app_deploy : Log in to Docker Hub] ...... changed
TASK [app_deploy : Pull Docker image] ......... changed
TASK [app_deploy : Stop existing container] ... changed
TASK [app_deploy : Remove existing container] . changed
TASK [app_deploy : Run application container] . changed
TASK [app_deploy : Wait for application] ...... ok
TASK [app_deploy : Verify application health] . ok
TASK [app_deploy : Show health check result] .. ok
msg: "App is running, status: 200"
PLAY RECAP
lab04-vm: ok=9  changed=5  unreachable=0  failed=0

### Container status (docker ps):
CONTAINER ID   IMAGE                              COMMAND
5a4b4b29701f   nadiaa02/lab02-python-app:latest   "python app.py"
STATUS: Up   PORTS: 0.0.0.0:5000->5000/tcp   NAMES: devops-app

### Health check:
```bash
$ curl http://93.77.181.6:5000/
{"service":{"name":"devops-info-service","version":"1.0.0"},"runtime":{"uptime_human":"0 hours, 1 minute"},...}

HTTP Status: 200 OK
```

---

## 6. Key Decisions

**Why use roles instead of plain playbooks?**
Roles enforce separation of concerns and make code reusable. The docker role can be used in any project that needs Docker, without copying tasks. Plain playbooks become monolithic and hard to maintain.

**How do roles improve reusability?**
Each role is self-contained with its own tasks, handlers, and defaults. Any playbook can include a role with one line. Roles can also be shared via Ansible Galaxy.

**What makes a task idempotent?**
A task is idempotent when it checks current state before acting. Ansible modules like `apt`, `service`, and `user` do this automatically — they only make changes when the current state differs from the desired state.

**How do handlers improve efficiency?**
Handlers only run when notified, and only once per play even if notified multiple times. This prevents unnecessary service restarts — Docker is only restarted if packages actually changed.

**Why is Ansible Vault necessary?**
Plaintext credentials in Git are a critical security risk. Vault encrypts secrets at rest so they can be version-controlled safely. The vault password is kept separate and never committed.

---

## 7. Challenges

- Ansible 2.20 has a bug where group_vars vault variables are not resolved in task args — worked around by defining vars directly in playbook
- Docker GPG key deprecation warning in apt_key module — cosmetic only, does not affect functionality
