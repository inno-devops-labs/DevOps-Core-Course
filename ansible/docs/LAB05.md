# Lab 05 - Tasks 1-3

## 1. Ansible installation check

```bash
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible --version
ansible [core 2.16.3]
```

## 2. Role-based structure created

```text
ansible/
  inventory/hosts.ini
  roles/common/{tasks,defaults}/main.yml
  roles/docker/{tasks,handlers,defaults}/main.yml
  roles/app_deploy/{tasks,handlers,defaults}/main.yml
  playbooks/{site,provision,deploy}.yml
  group_vars/all.yml
  ansible.cfg
```

## 3. Inventory configured

`inventory/hosts.ini` contains `webservers` group and SSH variables.

Before running against your VM, replace:
- `ansible_host=203.0.113.10`
- `ansible_user=ubuntu` (if different)
- uncomment and set `ansible_ssh_private_key_file`

## 4. Connectivity commands

Run from `ansible/`:

```bash
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible all -m ping
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible webservers -a "uname -a"
```

Expected result: `SUCCESS` for the target host.

## 5. Common role implemented (Task 2.1)

`roles/common/tasks/main.yml` now performs:
- apt cache update (`cache_valid_time` supported)
- installation of essential packages from `common_packages`
- timezone reconciliation using `timedatectl` only when drift is detected

`roles/common/defaults/main.yml` defines:
- package list (`python3-pip`, `curl`, `git`, `vim`, `htop`, etc.)
- cache validity time and timezone options

## 6. Docker role implemented (Task 2.2)

`roles/docker/tasks/main.yml` now performs:
- Docker prerequisite packages installation
- Docker GPG key installation (`/etc/apt/keyrings/docker.asc`)
- Docker apt repository setup (`download.docker.com`)
- Docker engine packages installation (`docker-ce`, `docker-ce-cli`, `containerd.io`, plugins)
- Docker service enable/start
- user membership in `docker` group
- `python3-docker` installation

`roles/docker/handlers/main.yml`:
- `restart docker` handler restarts Docker when notified

`roles/docker/defaults/main.yml` defines:
- architecture mapping and repository string
- Docker packages and docker users

## 7. Provisioning playbook (Task 2.3)

`playbooks/provision.yml`:
- targets `webservers`
- enables privilege escalation
- applies roles in order: `common`, `docker`

## 8. Idempotency run commands (Task 2.4)

Run from `ansible/`:

```bash
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible-playbook playbooks/provision.yml
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible-playbook playbooks/provision.yml
```

Expected behavior:
- first run: several tasks in `changed`
- second run: tasks mostly `ok`, `changed=0` (or near zero if external state changed)

Paste terminal output from both runs below for final submission evidence.

## 9. Vaulted variables (Task 3.1)

`group_vars/all.yml` is now Ansible Vault encrypted and contains:
- `dockerhub_username`
- `dockerhub_password`
- app deployment configuration (`app_name`, `docker_image_tag`, ports, restart policy)

`ansible.cfg` is configured with:
- `vault_password_file = .vault_pass`

Current placeholder vault password used to bootstrap this file:
- `lab05-temporary-pass`

Replace placeholders with your real credentials:

```bash
cd ansible/
cp .vault_pass.example .vault_pass
chmod 600 .vault_pass
ansible-vault edit group_vars/all.yml --vault-password-file .vault_pass
```

Then rekey to your own password:

```bash
ansible-vault rekey group_vars/all.yml --vault-password-file .vault_pass
```

## 10. App deploy role implemented (Task 3.2)

`roles/app_deploy/tasks/main.yml` now performs:
- Docker Hub login using vaulted credentials (`no_log: true`)
- image pull (`community.docker.docker_image`, `source: pull`)
- old container stop/remove when redeploy is required
- container run with:
  - `5000:5000` mapping
  - environment variables
  - restart policy `unless-stopped`
- readiness wait on app port
- health check (`/health`) and main endpoint (`/`) verification

`roles/app_deploy/handlers/main.yml`:
- `restart app container` handler defined

`roles/app_deploy/defaults/main.yml` defines:
- image and tag defaults
- restart policy
- environment values
- health-check URLs

## 11. Deploy playbook and run (Task 3.3-3.4)

Deploy role is wired in `playbooks/deploy.yml`.

Run from `ansible/`:

```bash
cp .vault_pass.example .vault_pass
chmod 600 .vault_pass
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible-playbook playbooks/deploy.yml
```

Or prompt manually:

```bash
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Verification commands:

```bash
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ansible webservers -a "docker ps"
curl http://<VM-IP>:5000/health
curl http://<VM-IP>:5000/
```
