# Lab 5 — Ansible Fundamentals (Documentation)

## 1. Architecture Overview

- **Ansible version:** 2.16+ (run `ansible --version` to confirm).
- **Target VM OS and version:** Ubuntu 22.04 LTS (VM from Lab 4, Pulumi + Yandex Cloud).
- **Role structure:**
  - **common** — base system setup: force IPv4 for apt, optional Yandex mirror, apt cache update, install packages (curl, git, vim, htop, etc.), timezone.
  - **docker** — install Docker CE from official repository, refresh cache after adding repo, install packages (docker-ce, docker-ce-cli, containerd.io), docker service, add user to docker group, python3-docker.
  - **app_deploy** — verify Vault variables, Docker Hub login, pull image, stop/remove old container, run new one with port 5001, wait for port, check /health.
- **Why roles instead of monolithic playbooks?** Roles enable code reuse, separate testability, and short playbooks; logic is split by concern (common / docker / app), and one role can be used across multiple playbooks and projects.

## 2. Roles Documentation

### common
- **Purpose:** Base system setup: force IPv4 for apt (avoid IPv6 "Network is unreachable"), optional Yandex mirror for Ubuntu, apt cache update, install packages (python3-pip, curl, git, vim, htop, unzip, ca-certificates, gnupg, lsb-release), set timezone (Europe/Moscow).
- **Variables:** `use_yandex_mirror` (default: true), `common_packages` (list), `timezone` (default: Europe/Moscow). In `defaults/main.yml`.
- **Handlers:** None.
- **Dependencies:** None.

### docker
- **Purpose:** Install Docker CE: dependencies (ca-certificates, curl, gnupg), GPG key and Docker repository, apt cache update, install docker-ce, docker-ce-cli, containerd.io, start and enable docker service, add user (ansible_user) to docker group, install python3-docker for Ansible modules.
- **Variables:** In `defaults/main.yml`: `docker_install_compose`, `docker_users`. Tasks use architecture mapping (x86_64→amd64, aarch64→arm64) for repository URL.
- **Handlers:** `restart docker` — restart docker service when repository or packages change.
- **Dependencies:** None (common role typically runs first to update apt).

### app_deploy
- **Purpose:** Deploy application in Docker: verify dockerhub_username and dockerhub_password, Docker Hub login (no_log), pull image, stop and remove old container by name, run new container with port mapping (app_port:app_container_port, default 5001:5001), restart policy unless-stopped, wait for port, GET /health check.
- **Variables:** From group_vars (Vault): `dockerhub_username`, `dockerhub_password`, `app_name`, `docker_image`, `docker_image_tag`, `app_port`, `app_container_name`. In role defaults: `app_port`, `app_container_port` (5001), `app_restart_policy`, `app_env`.
- **Handlers:** `restart app container` (optional, conditional).
- **Dependencies:** Requires docker role (Docker on host) and encrypted group_vars/all.yml with credentials.

## 3. Idempotency Demonstration

- **First run:** On first run of `ansible-playbook playbooks/provision.yml --ask-vault-pass`, tasks show **changed**: apt cache update, package installs (common, Docker dependencies, Docker repo, Docker packages, python3-docker), mirror setup/force IPv4 when use_yandex_mirror, docker service start, user added to docker group, timezone set.
- **Second run:** On second run the same tasks show **ok** — state already matches desired, no (or minimal) changes.
- **Analysis:** First run brings packages, repos, service, and user to desired state; second run shows modules (apt, service, user, template/copy) see target state is met and do not change the system.
- **Explanation:** Idempotency comes from declarative modules with explicit state: `apt: state=present`, `service: state=started`, `user: groups: docker`, `template`/`copy` with fixed content. Ansible applies changes only when current and desired state differ.

## 4. Ansible Vault Usage

- **Storage:** Docker Hub credentials and app variables are stored in `group_vars/all.yml`, encrypted with `ansible-vault create` (or `ansible-vault encrypt`). The file can be committed; without the Vault password the content is unreadable.
- **Vault password management:** Use `--ask-vault-pass` when running playbooks and ad-hoc commands; alternative: password file (e.g. `.vault_pass`), `chmod 600`, and `--vault-password-file` or `vault_password_file` in ansible.cfg. Password file is in `.gitignore`.
- **Example encrypted file:** `head -5 group_vars/all.yml` shows lines like `$ANSIBLE_VAULT;1.1;AES256` or `$ANSIBLE_VAULT;1.2;AES256` — file is encrypted. To verify decryption: `ansible-vault view group_vars/all.yml --ask-vault-pass`.
- **Why Ansible Vault is important:** Keeps secrets (Docker Hub login/password) in the repo in encrypted form; decryption only with the Vault password, reducing leakage risk when collaborating and backing up.

## 5. Deployment Verification

- **Deploy run output:** Output of `ansible-playbook playbooks/deploy.yml --ask-vault-pass`: tasks Ensure Docker Hub credentials, Log in to Docker Hub, Pull Docker image, Stop existing container (if any), Remove old container, Run application container, Wait for application port, Check health endpoint — all succeed (ok or changed as needed).
- **Container status:** Example output of `ansible webservers -a "docker ps" --ask-vault-pass`:
  ```text
  web1 | CHANGED | rc=0 >>
  CONTAINER ID   IMAGE                    COMMAND                  CREATED         STATUS         PORTS                    NAMES
  <id>           <user>/devops-info-service:latest   "python app.py"    ...         Up ...         0.0.0.0:5001->5001/tcp   devops-app
  ```
- **Health check verification:** From local machine:
  ```bash
  curl http://89.169.129.155:5001/health
  ```
  Example response:
  ```json
  {"status":"healthy","timestamp":"2026-02-25T10:07:38.381157.000Z","uptime_seconds":91485.11}
  ```
  Main page: `curl http://89.169.129.155:5001/` — returns service info.
- **Handlers:** For deploy, the "restart app container" handler is not needed in the typical flow (container is recreated by Run application container). The "restart docker" handler in the docker role runs when Docker repo or packages change during provisioning.

## 6. Key Decisions

- **Why roles instead of plain playbooks?** Roles group related tasks, defaults, and handlers by concern (common / docker / app); playbooks stay short and readable; the same roles can be used in different playbooks and projects.
- **How do roles improve reusability?** One role can be included in multiple playbooks and optionally published to Ansible Galaxy; a change in the role applies everywhere it is used.
- **What makes a task idempotent?** Using modules that describe desired state (e.g. `state: present`, `state: started`) instead of one-off commands; Ansible only applies changes when current and target state differ.
- **How do handlers improve efficiency?** Handlers run once at the end of the playbook even with multiple notifies (e.g. one Docker restart after several config or package changes).
- **Why is Ansible Vault necessary?** To store secrets in the repo encrypted and avoid keeping passwords and tokens in plain text in code and commit history.

## 7. Challenges

- **"Failed to update apt cache" on VM:** The VM had no outbound internet. In Pulumi the security group had only ingress rules; an egress rule was added (protocol ANY, 0.0.0.0/0). The common role also uses Yandex mirror and forces IPv4 for apt to reduce dependence on IPv6 and external mirrors.
- **docker-ce package not found:** The Docker repo URL used architecture from ansible_architecture (x86_64/aarch64) while Docker expects amd64/arm64. Mapping was added in the "Add Docker repository" task. After adding the repo, explicit apt cache update (cache_valid_time: 0) was added so packages from the new repo are visible.
- **Variables from group_vars not loaded:** In deploy.yml playbook, explicit `vars_files: ../group_vars/all.yml` was added so variables from the encrypted file are used on deploy regardless of current directory and load order.
- **"Cannot create container when image is not specified" in Stop existing container:** The docker_container module with state: stopped requires the image parameter. The image parameter was added to the "Stop existing container" task.
- **Accessing the app from outside (curl on port 5001):** In Pulumi the security group only had port 5000 open; the app listens on 5001. An ingress rule for TCP 5001 (app-5001-rule) was added in `pulumi/__main__.py` and applied with `pulumi up`.
