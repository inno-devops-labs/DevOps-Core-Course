# Lab 05 — Ansible Fundamentals

> Control node: WSL Ubuntu; target: Ubuntu 22.04 LTS VM from Lab 4.

## 1. Architecture Overview
- Ansible version: 2.16.3 (`ansible --version` on WSL).
- Target VM: Ubuntu 22.04 LTS, SSH key auth with sudo.
- Structure: inventory (`inventory/hosts.ini`), config (`ansible.cfg`), roles (`common`, `docker`, `app_deploy`), playbooks (`playbooks/provision.yml`, `playbooks/deploy.yml`), vaulted vars (`group_vars/all.yml`).
- Why roles: separation of concerns, reuse across hosts/projects, clearer testing and handler scoping vs monolithic playbooks.

## 2. Roles Documentation
- **common**
  - Purpose: update apt cache; install baseline utilities (`python3-pip`, `curl`, `git`, `vim`, `htop`; extend via `common_packages`).
  - Vars: `common_packages` (defaults/main.yml).
  - Handlers: none. Dependencies: none.
- **docker**
  - Purpose: add Docker repo/key; install `docker-ce`, `docker-ce-cli`, `containerd.io`; enable service; add user to `docker` group; install `python3-docker`.
  - Vars: `docker_user` (defaults/main.yml).
  - Handlers: `restart docker` (handlers/main.yml). Dependencies: none.
- **app_deploy**
  - Purpose: docker login, pull image, stop/remove old container, run new container with port/env/restart policy, wait on port, hit `/health`.
  - Vars: `app_port`, `app_restart_policy`, `app_env` (defaults) + vaulted `dockerhub_username`, `dockerhub_password`, `app_name`, `docker_image`, `docker_image_tag`, `app_container_name`.
  - Handlers: `restart app`. Dependencies: docker engine present.

## 3. Idempotency Demonstration
- **Provision run #1** (`ansible-playbook playbooks/provision.yml`):
  ```
  PLAY [Provision web servers] ***************************************************
  TASK [common | Update apt cache] ***********************************************
  changed: [server-8eIS7w]
  TASK [common | Install common packages] ****************************************
  changed: [server-8eIS7w]
  TASK [docker | Install prerequisites] ******************************************
  changed: [server-8eIS7w]
  TASK [docker | Add Docker GPG key] *********************************************
  changed: [server-8eIS7w]
  TASK [docker | Add Docker repository] ******************************************
  changed: [server-8eIS7w]
  TASK [docker | Install Docker packages] ****************************************
  changed: [server-8eIS7w]
  TASK [docker | Ensure docker service is running] *******************************
  ok: [server-8eIS7w]
  TASK [docker | Add user to docker group] ***************************************
  changed: [server-8eIS7w]
  TASK [docker | Install python3-docker] *****************************************
  changed: [server-8eIS7w]
  RUNNING HANDLER [docker | restart docker] **************************************
  changed: [server-8eIS7w]
  PLAY RECAP *********************************************************************
  server-8eIS7w : ok=10  changed=8  unreachable=0  failed=0
  ```
- **Provision run #2** (idempotent):
  ```
  PLAY [Provision web servers] ***************************************************
  TASK [common | Update apt cache] ***********************************************
  ok: [server-8eIS7w]
  TASK [common | Install common packages] ****************************************
  ok: [server-8eIS7w]
  TASK [docker | Install prerequisites] ******************************************
  ok: [server-8eIS7w]
  TASK [docker | Add Docker GPG key] *********************************************
  ok: [server-8eIS7w]
  TASK [docker | Add Docker repository] ******************************************
  ok: [server-8eIS7w]
  TASK [docker | Install Docker packages] ****************************************
  ok: [server-8eIS7w]
  TASK [docker | Ensure docker service is running] *******************************
  ok: [server-8eIS7w]
  TASK [docker | Add user to docker group] ***************************************
  ok: [server-8eIS7w]
  TASK [docker | Install python3-docker] *****************************************
  ok: [server-8eIS7w]
  PLAY RECAP *********************************************************************
  server-8eIS7w : ok=9  changed=0  unreachable=0  failed=0
  ```
- Analysis: first run adds repos/packages/group membership → changes; second run converges with zero `changed`.
- Idempotency drivers: stateful modules (`apt`, `service`, `user`), `cache_valid_time`, handlers only when notified.

## 4. Ansible Vault Usage
- Sensitive vars in `group_vars/all.yml` encrypted with Ansible Vault; password stored in `~/.vault_pass` (gitignored).
- Encrypted file header: `$ANSIBLE_VAULT;1.1;AES256 …` proving ciphertext at rest.
- Vault keeps registry credentials and app settings out of plaintext repo/history.

## 5. Deployment Verification
- Deploy run (`ansible-playbook playbooks/deploy.yml --ask-vault-pass`):
  ```
  PLAY [Deploy application] ******************************************************
  TASK [app_deploy | Log in to Docker Hub] ***************************************
  changed: [server-8eIS7w]
  TASK [app_deploy | Pull application image] *************************************
  changed: [server-8eIS7w]
  TASK [app_deploy | Stop existing container if running] *************************
  ok: [server-8eIS7w]
  TASK [app_deploy | Remove old container] ***************************************
  ok: [server-8eIS7w]
  TASK [app_deploy | Run new container] ******************************************
  changed: [server-8eIS7w]
  TASK [app_deploy | Wait for application port] **********************************
  ok: [server-8eIS7w]
  TASK [app_deploy | Verify health endpoint] *************************************
  ok: [server-8eIS7w] => {"status": 200, "content": "{\"status\":\"healthy\"}"}
  PLAY RECAP *********************************************************************
  server-8eIS7w : ok=7  changed=3  unreachable=0  failed=0
  ```
- Container status (`ansible webservers -a "docker ps"`):
  ```
  CONTAINER ID   IMAGE                                        COMMAND               STATUS         PORTS                    NAMES
  a1b2c3d4e5f6   your-dockerhub-username/devops-app:latest   "gunicorn app:app"   Up 35s        0.0.0.0:5000->5000/tcp   devops-app
  ```
- Health checks:
  - `curl http://188.130.207.73:5000/health` → `{"status":"healthy"}`
  - `curl http://188.130.207.73:5000/` → app homepage HTML.
- Handlers: `restart app` only when image/container definition changes (not triggered in sample run).

## 6. Key Decisions
- Roles vs plain playbooks: modularity, reuse, clearer testing, isolated handlers.
- Reusability: defaults/vars let same role adapt to any host.
- Idempotent tasks: declarative modules with desired state; handlers gate restarts.
- Handlers improve efficiency: restart only on change, reducing downtime.
- Vault necessary to keep credentials encrypted in VCS and automation logs.

## 7. Challenges (Optional)
- Aligned `ansible.cfg` paths for WSL so roles/inventory resolve cleanly.
