# Lab 05 – Ansible Fundamentals – Documentation

## 1. Architecture Overview

- **Ansible version:** 2.16+ (tested with 2.16)
- **Target VM:** Ubuntu 24.04 LTS on Yandex Cloud (from Lab 4)
- **Role-based structure:** Three independent roles (`common`, `docker`, `app_deploy`) each containing tasks, defaults, and handlers. This promotes reusability, maintainability, and clear separation of concerns.

## 2. Roles Documentation

### `common`

- **Purpose:** Prepares the base system: updates package cache and installs essential tools.
- **Variables:**
  - `common_packages` (list) – defined in `defaults/main.yml`
- **Handlers:** none
- **Dependencies:** none

### `docker`

- **Purpose:** Installs Docker CE from the official repository, ensures the service is running, and adds the user to the `docker` group.
- **Variables:**
  - `docker_user` (default: `ubuntu`)
  - `docker_packages` (list of Docker components)
- **Handlers:**
  - `restart docker` – restarts the Docker daemon
- **Dependencies:** requires `common` (for `python3-pip`)

### `app_deploy`

- **Purpose:** Logs into Docker Hub, pulls the application image, and runs a container with port mapping and health checks.
- **Variables:**
  - `app_name`, `docker_image_tag`, `app_port`, `app_container_name`, `restart_policy`
- **Handlers:**
  - `restart app` – can be used to restart the container (not actively used in current tasks)
- **Dependencies:** requires `docker`

## 3. Idempotency Demonstration

### First run of `provision.yml`

```bash
$ ansible-playbook playbooks/provision.yml
...
PLAY RECAP ********************************************
lab-vm : ok=11 changed=9 unreachable=0 failed=0
```

Tasks that changed: apt update, package installations, Docker repo/key, Docker service start, user group modification.
(Output shortened for brevity.)

### Second run of `provision.yml`

```
$ ansible-playbook playbooks/provision.yml
...
PLAY RECAP ********************************************
lab-vm : ok=11 changed=0 unreachable=0 failed=0
```

**Analysis:**

* The first run performed all necessary changes because the system was fresh.
* The second run showed **0 changes** because every task is written idempotently:
  * `apt` with `state=present` only installs missing packages.
  * `apt_key` and `apt_repository` check existence before adding.
  * `service` ensures the service is started/enabled without restarting if already correct.
  * `user` adds the user to the group only if not already a member.

## 4. Ansible Vault Usage

Sensitive data (Docker Hub credentials) are stored encrypted in `group_vars/all.yml`.
**Vault password management:**

* Used `ansible-vault create` to create the encrypted file.
* Password is stored in a local `.vault_pass` file (added to `.gitignore`) to avoid typing it every time.
* In `ansible.cfg` we can optionally set `vault_password_file = .vault_pass`.

```
$ cat group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
66386439653236336...
```

Using Vault ensures secrets are never exposed in version control.

## 5. Deployment Verification

```
$ ansible-playbook playbooks/deploy.yml --ask-vault-pass
...
TASK [app_deploy : Check health endpoint] *************
ok: [lab-vm]

PLAY RECAP ********************************************
lab-vm : ok=8 changed=4 unreachable=0 failed=0
```

**Container status:**

```
$ ansible webservers -a "docker ps"
lab-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                     COMMAND   CREATED         STATUS         PORTS                                       NAMES
a1b2c3d4e5f6   plaffyyy9/devops-info-service:latest   ...      10 seconds ago  Up 9 seconds   0.0.0.0:5000->5000/tcp   devops-info-service
```

**Health check:**

```
$ curl http://93.77.188.243:5000/health
{"status":"healthy","timestamp":"2026-02-26T20:14:01.812949+00:00","uptime_seconds":89}
```

## 6. Key Decisions

* **Why use roles instead of plain playbooks?**
  Roles encapsulate functionality, making the code reusable, testable, and easier to maintain. They follow a standard structure that any Ansible user can immediately understand.
* **How do roles improve reusability?**
  The same `docker` role can be used in any project that needs Docker, simply by adding it to the playbook. Variables allow customization without modifying the role itself.
* **What makes a task idempotent?**
  A task is idempotent if running it multiple times produces the same result without unintended side effects. In Ansible this is achieved by using modules that check the current state before making changes (e.g., `apt: state=present` instead of shell commands).
* **How do handlers improve efficiency?**
  Handlers run only when notified by a task that actually made a change. This avoids unnecessary service restarts and speeds up playbook execution.
* **Why is Ansible Vault necessary?**
  It allows storing secrets (passwords, tokens) directly in the repository in encrypted form, ensuring they are not exposed while still being versioned and shared with the team.

## 7. Challenges (Optional)

* **Issue:** The Docker repository URL requires the Ubuntu release name.
  **Solution:** Used `{{ ansible_distribution_release }}` fact to dynamically insert the correct name (e.g., `jammy` for 22.04, `noble` for 24.04).
* **Issue:** The `docker_login` module requires the `community.docker` collection.
  **Solution:** Installed it with `ansible-galaxy collection install community.docker`.
