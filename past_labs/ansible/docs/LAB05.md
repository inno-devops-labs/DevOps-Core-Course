# LAB05 - Ansible Fundamentals

> Repo: `ansible/`  
> Control node: WSL (Ubuntu)  
> Target node: VirtualBox VM (Ubuntu)

---

## 1. Architecture overview

### Versions / environment
- **Ansible:** `ansible [core 2.16.3]`
- **Target VM OS:** Ubuntu **24.04.4 LTS**
- **Docker Engine:** 29.2.1 (installed by Ansible)
- **Docker Python SDK on VM:** 5.0.3 (required for `community.docker` modules) 

### Project structure
```
ansible/
├── ansible.cfg
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml               # encrypted via Ansible Vault
├── playbooks/
│   ├── provision.yml         # runs roles: common + docker
│   └── deploy.yml            # runs role: app_deploy
├── roles/
│   ├── common/
│   ├── docker/
│   └── app_deploy/
└── docs/
    └── LAB05.md
```
This structure follows the lab requirement to use **roles** instead of a monolithic playbook.

### Why roles (instead of monolithic playbooks)?
Roles make automation:
- **Reusable** (same role can be reused across playbooks/projects),
- **Readable** (clear separation of concerns),
- **Maintainable** (each role can be changed/tested independently),
- **Scalable** (easy to compose `common + docker + app_deploy`).

---

## 2. Inventory & configuration

### Inventory (`inventory/hosts.ini`)
Example:
```ini
[webservers]
vm1 ansible_host=172.21.112.1 ansible_port=2222 ansible_user=liza
```

### Ansible config (`ansible.cfg`)
Key settings:
```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
retry_files_enabled = False
remote_user = liza
vault_password_file = .vault_pass

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```
> Note: `vault_password_file` is one of the recommended approaches in the lab.  

### Connectivity test
```bash
ansible all -m ping
ansible webservers -a "uname -a"
```

---

## 3. Roles documentation

The lab requires 3 roles: **common**, **docker**, **app_deploy**, each with tasks/handlers/defaults as needed.

### 3.1 Role: `common`

**Purpose:** baseline VM provisioning (APT cache, essential packages, timezone). 

**Key tasks (examples):**
- Update apt cache (`apt: update_cache=yes`)
- Install common packages (`apt: state=present`)
- Set timezone (optional)

**Variables (defaults):**
- `common_packages`: list of packages to install (curl/git/vim/htop/python3-pip/etc.)

**Handlers:** none (not needed).

**Dependencies:** none.

---

### 3.2 Role: `docker`

**Purpose:** install and configure Docker Engine on Ubuntu, enable service, add user to docker group, install `python3-docker`.

**Key tasks (examples):**
- Install prerequisites
- Add Docker GPG key
- Add Docker apt repository
- Install Docker packages
- Enable/start Docker service
- Add user to `docker` group
- Install `python3-docker` for Ansible Docker modules

**Variables (defaults):**
- `docker_user`: user to add to docker group (e.g., `liza`)

**Handlers:**
- `restart docker` (triggered when repo/key/packages change)

**Dependencies:** none.

---

### 3.3 Role: `app_deploy`

**Purpose:** deploy a containerized Python app from Docker Hub:
- login to registry using vaulted credentials
- pull image
- run container with port mapping + restart policy
- verify readiness via HTTP health endpoint  

**Key tasks (implemented):**
1. `docker_login` (with `no_log: true`)
2. `docker_image` pull
3. `docker_container` run
4. short `pause` to avoid early health-check race
5. `uri` health check to `/health`

**Variables (defaults + vaulted):**
- vaulted: `dockerhub_username`, `dockerhub_password`
- app: `docker_image`, `docker_image_tag`, `app_container_name`
- ports: `app_port`, `container_port`
- `restart_policy` (default: `unless-stopped`)
- `app_env` (optional env vars dict)

**Handlers:**
- `restart app container` (used if container definition changes)

**Dependencies:**
- Requires Docker installed (role `docker` should be applied first via `provision.yml`).

---

## 4. Playbooks

### 4.1 `playbooks/provision.yml`
```yaml
- name: Provision web servers
  hosts: webservers
  become: yes
  roles:
    - common
    - docker
```
Matches lab requirements: provisioning logic must live in roles. fileciteturn5file9

### 4.2 `playbooks/deploy.yml`
Because `group_vars/all.yml` is stored at the project root, I explicitly include it:
```yaml
- name: Deploy application
  hosts: webservers
  become: yes

  vars_files:
    - ../group_vars/all.yml

  roles:
    - app_deploy
```

---

## 5. Idempotency demonstration (Provision)

The lab requires running provisioning twice and documenting that the second run results in **zero changes**. 

### First run (`changed > 0`)
Command:
```bash
ansible-playbook playbooks/provision.yml
```

Result (summary):
- `vm1 : ok=13 changed=6 failed=0`

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ******************************************************************

TASK [Gathering Facts] ************************************************************************
ok: [vm1]

TASK [common : Update apt cache] **************************************************************
ok: [vm1]

TASK [common : Install common packages] *******************************************************
ok: [vm1]

TASK [common : Set timezone (optional)] *******************************************************
ok: [vm1]

TASK [docker : Install prerequisites] *********************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] ***********************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] ************************************************************
changed: [vm1]

TASK [docker : Add Docker apt repository] *****************************************************
changed: [vm1]

TASK [docker : Install Docker packages] *******************************************************
changed: [vm1]

TASK [docker : Ensure Docker is enabled and running] ******************************************
ok: [vm1]

TASK [docker : Add user to docker group] ******************************************************
changed: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] **************************
changed: [vm1]

RUNNING HANDLER [docker : restart docker] *****************************************************
changed: [vm1]

PLAY RECAP ************************************************************************************
vm1                        : ok=13   changed=6    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second run (`changed = 0`)
Command:
```bash
ansible-playbook playbooks/provision.yml
```

Result (summary):
- `vm1 : ok=12 changed=0 failed=0`

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ******************************************************************

TASK [Gathering Facts] ************************************************************************
ok: [vm1]

TASK [common : Update apt cache] **************************************************************
ok: [vm1]

TASK [common : Install common packages] *******************************************************
ok: [vm1]

TASK [common : Set timezone (optional)] *******************************************************
ok: [vm1]

TASK [docker : Install prerequisites] *********************************************************
ok: [vm1]

TASK [docker : Ensure /etc/apt/keyrings exists] ***********************************************
ok: [vm1]

TASK [docker : Add Docker GPG key] ************************************************************
ok: [vm1]

TASK [docker : Add Docker apt repository] *****************************************************
ok: [vm1]

TASK [docker : Install Docker packages] *******************************************************
ok: [vm1]

TASK [docker : Ensure Docker is enabled and running] ******************************************
ok: [vm1]

TASK [docker : Add user to docker group] ******************************************************
ok: [vm1]

TASK [docker : Install python docker SDK for Ansible docker modules] **************************
ok: [vm1]

PLAY RECAP ************************************************************************************
vm1                        : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Why the second run has no changes
All tasks use **stateful modules** (e.g., `apt state=present`, `service state=started enabled=yes`) so Ansible converges the system to the desired state and then reports **ok** on repeated runs.

### Why my roles are idempotent
- **State-driven modules (declarative)**
  - `apt` is used with `state: present` (packages are installed only if missing).
  - `service`/`systemd` is used with `state: started` and `enabled: yes` (service is started/enabled only if needed).
  - `file` is used with `state: directory` (directory is created only if missing, and permissions are enforced).
- **Docker modules that converge to a desired state**
  - `community.docker.docker_image` with `source: pull` ensures the image exists locally (it won’t “re-pull” unnecessarily when nothing changed).
  - `community.docker.docker_container` ensures the container is in the desired state (`started`, correct image, ports, env, restart policy).
- **Handlers instead of unconditional restarts**
  - Docker is restarted **only when notified** (e.g., after repo/key/package changes), not on every run. This keeps repeated runs stable and fast.
- **Explicit readiness checks (without forcing changes)**
  - `wait_for`/`pause`/`uri` validate that the service is up, but they do not modify system state. They prevent race conditions without breaking idempotency.

### Evidence in logs
- `provision.yml` second run: `changed=0` (system is already converged).
- `deploy.yml` may show changes if a new image/container revision is applied; otherwise it should converge and remain stable.

---

## 6. Ansible Vault usage

The lab requires storing Docker Hub credentials in an encrypted file.  

### Vaulted variables file
File: `group_vars/all.yml` (encrypted)

Example of encrypted header:
```
$ANSIBLE_VAULT;1.1;AES256
...
```
![encrypted](/ansible/docs/screenshots/cat_vars.png)

Decrypted contents (example / sanitized):
```yaml
dockerhub_username: "wkwtfigo"
dockerhub_password: "<DOCKERHUB_ACCESS_TOKEN>"

app_name: "devops-info-service"
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: "latest"
app_port: 5000
container_port: 5000
app_container_name: "{{ app_name }}"
```

### Vault password management
I use a local password file:
```bash
printf "my-vault-password" > .vault_pass
chmod 600 .vault_pass
```

`.vault_pass` is excluded from git:
```
.vault_pass
*.retry
__pycache__/
```
This is aligned with the lab’s security guidance (do not commit secrets).

Ansible Vault solves a practical security problem: we want to keep infrastructure code in Git (so it’s reviewable and reproducible), but we **must not** store secrets in plain text.

### What Vault protects in this lab
- Docker Hub credentials:
  - `dockerhub_username`
  - `dockerhub_password` (recommended as an **access token**)

### Why Vault matters
- **Prevents accidental secret leaks**
  - Plain-text secrets can be leaked through git history, screenshots, CI logs, or shared archives.
- **Enables safe collaboration**
  - The team can clone the repo and run playbooks, while only authorized people who have the vault password can decrypt secrets.
- **Audit-friendly**
  - Secrets are encrypted at rest, while the rest of the automation stays transparent and reviewable in version control.
- **Supports secret rotation**
  - If a token is rotated, you update the vaulted file once; roles/playbooks remain unchanged.

### Best practices applied
- The vault password is stored locally in `.vault_pass` with `chmod 600`.
- `.vault_pass` is excluded from Git via `.gitignore`.
- `no_log: true` is used for the Docker login task so secrets don’t appear in Ansible output.
- If a token is exposed, it should be revoked immediately and replaced in Vault.

---

## 7. Deployment verification

### Deploy run
Command:
```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

Result (summary):
- `vm1 : ok=7 changed=3 failed=0`
- Health check: `ok` (no retries after adding a small startup pause)

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] *******************************************************************************************************************************************************************************************

TASK [Gathering Facts] **********************************************************************************************************************************************************************************************
ok: [vm1]

TASK [app_deploy : Login to Docker Hub] *****************************************************************************************************************************************************************************
changed: [vm1]

TASK [app_deploy : Pull application image] **************************************************************************************************************************************************************************
ok: [vm1]

TASK [app_deploy : Ensure app container is running] *****************************************************************************************************************************************************************
changed: [vm1]

TASK [app_deploy : Give app time to start] **************************************************************************************************************************************************************************
Pausing for 5 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [vm1]

TASK [app_deploy : Health check] ************************************************************************************************************************************************************************************
ok: [vm1]

RUNNING HANDLER [app_deploy : restart app container] ****************************************************************************************************************************************************************
changed: [vm1]

PLAY RECAP **********************************************************************************************************************************************************************************************************
vm1                        : ok=7    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

zagur@LAPTOP-JONCQBVT:~/projects/ansible$
```

### Container status
Command:
```bash
ansible webservers -a "docker ps"
```

Output:
```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible webservers -a "docker ps"
vm1 | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                 COMMAND           CREATED          STATUS                    PORTS                    NAMES
42e3cf173671   wkwtfigo/devops-info-service:latest   "python app.py"   34 seconds ago   Up 25 seconds (healthy)   0.0.0.0:5000->5000/tcp   devops-info-service
```

### Health endpoint verification
Because the VM is accessed via **VirtualBox NAT + SSH port forwarding**, port `5000` is not directly reachable from the host without extra forwarding.
Verification options:

**Option A (recommended in report): run curl on VM through Ansible**
```bash
ansible webservers -m shell -a "curl -sS -m 3 http://127.0.0.1:5000/health && echo"
ansible webservers -m shell -a "curl -sS -m 3 http://127.0.0.1:5000/ && echo"
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible webservers -m shell -a "curl -sS -m 3 http://127.0.0.1:5000/health && echo"
vm1 | CHANGED | rc=0 >>
{"status":"healthy","timestamp":"2026-02-20T14:29:09.512Z","uptime_seconds":63}
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ 
```

```bash
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ ansible webservers -m shell -a "curl -sS -m 3 http://127.0.0.1:5000 && echo"
vm1 | CHANGED | rc=0 >>
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"42e3cf173671","platform":"Linux","platform_version":"#14~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Jan 15 15:52:10 UTC 2","architecture":"x86_64","cpu_count":3,"python_version":"3.13.11"},"runtime":{"uptime_seconds":90,"uptime_human":"0 hours, 1 minutes","current_time":"2026-02-20T14:29:36.772Z","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
zagur@LAPTOP-JONCQBVT:~/projects/ansible$ 
```

**Option B: SSH tunnel**
```bash
ssh -p 2222 -L 5000:127.0.0.1:5000 liza@172.21.112.1
# in another terminal:
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/
```

---

## 8. Key decisions (short answers)

**Why use roles instead of plain playbooks?**  
Roles enforce a clean structure, encourage reuse, and keep playbooks minimal and readable.

**How do roles improve reusability?**  
Each role encapsulates one responsibility (baseline setup, Docker, app deploy) and can be reused across environments by changing variables.

**What makes a task idempotent?**  
A task is idempotent when re-running it keeps the system in the same desired state and Ansible reports `ok` instead of `changed`.

**How do handlers improve efficiency?**  
Handlers run only when notified (e.g., restart Docker only if packages/repo change), reducing unnecessary restarts.

**Why is Ansible Vault necessary?**  
It allows committing configuration to VCS while keeping secrets encrypted and safe, meeting security requirements.  

---

## 9. Challenges & solutions (brief)

- **Ansible ignored `ansible.cfg` (“world writable directory”)**  
  Moved project to WSL Linux filesystem and fixed permissions (`chmod go-w`) so Ansible loads config.

- **`dockerhub_username` undefined in deploy role**  
  `group_vars/all.yml` was not auto-loaded due to playbook path; resolved by `vars_files: ../group_vars/all.yml`.

- **Health check had a retry on first attempt**  
  Added a short `pause` before HTTP health check to avoid race condition during app startup.

---

## 10. How to reproduce

```bash
# 1) Provision VM
ansible-playbook playbooks/provision.yml

# 2) Run again to show idempotency
ansible-playbook playbooks/provision.yml

# 3) Deploy app
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

# 4) Verify
ansible webservers -a "docker ps"
ansible webservers -m shell -a "curl -sS -m 3 http://127.0.0.1:5000/health && echo"
```