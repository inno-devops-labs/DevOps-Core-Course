# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

- **Ansible version:** `ansible [core 2.20.2]` (Python 3.14.3, Homebrew install on macOS).
- **Target VM OS:** Ubuntu 25.04 aarch64 (Ubuntu reports that this release is end‑of‑life; Docker is installed from the `noble` repository to stay on a supported Docker CE channel).
- **Topology:**
  - Control node: macOS host with Ansible, Docker CLI and project sources.
  - Target node: local Ubuntu VM reachable over SSH (`maria@192.168.64.6`) with password sudo.
  - Application: containerised Python service exposed on `http://192.168.64.6:5000`.
- **Role structure:**
  - `common` — baseline system provisioning (APT cache, common packages, timezone).
  - `docker` — Docker CE installation and configuration.
  - `app_deploy` — pulling and running the application container, plus health checks.
- **Why roles instead of a single playbook:** roles keep provisioning, Docker setup and application deployment cleanly separated, reusable, and easier to test in isolation. Playbooks (`provision.yml`, `deploy.yml`, `site.yml`) become very short and only orchestrate which roles to run.

## 2. Roles Documentation

### common

- **Purpose:** Provide a minimal, consistent base configuration on every host before any application‑specific logic runs.
- **Main tasks:**
  - Remove a broken HashiCorp APT source file (`/etc/apt/sources.list.d/hashicorp.list`) if present, to avoid failing `apt update`.
  - Refresh APT cache with `cache_valid_time: 3600`.
  - Install a configurable list of baseline tools (`python3-pip`, `curl`, `git`, `vim`, `htop`, etc.).
  - Detect the current timezone using `timedatectl` and change it only when it differs from the desired value.
- **Variables (defaults):**
  - `common_packages` — list of Debian packages to ensure present.
  - `common_timezone` — system timezone (default `"UTC"`).
- **Handlers:** none.
- **Dependencies:** none; this role is expected to run first on every host.

### docker

- **Purpose:** Install a working Docker engine on the Ubuntu VM, configure the official Docker APT repository and enable non‑root Docker usage for the SSH user.
- **Main tasks:**
  - Install APT prerequisites (`ca-certificates`, `curl`, `gnupg`).
  - Ensure `/etc/apt/keyrings` exists and download the Docker GPG key there.
  - Configure the Docker APT repository with an architecture‑aware `arch=` value and a safe `signed-by=` reference to the keyring. For unsupported Ubuntu releases, fall back to using `noble` as the repo codename.
  - Install Docker CE packages (`docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`) and keep them in the desired state.
  - Enable and start the `docker` systemd service.
  - Add the SSH user to the `docker` group so that Docker commands can be run without `sudo`.
  - Install `python3-docker` so Ansible Docker modules can work on the target host.
- **Variables (defaults):**
  - `docker_group_user` — user that should be added to the `docker` group (derived from Ansible facts).
  - `docker_install_state` — package state, `present` by default.
  - `docker_apt_release` — codename used for the Docker APT repo (defaults to the host’s distribution release, but a fact‑driven helper chooses a supported fallback if needed).
- **Handlers:**
  - `restart docker` — restarts the Docker service whenever the Docker repo or packages change.
- **Dependencies:** assumes the `common` role has run and APT is healthy.

### app_deploy

- **Purpose:** Log in to Docker Hub, pull the application image, manage the lifecycle of the application container, and validate that the service is healthy.
- **Main tasks:**
  - Authenticate to Docker Hub using credentials stored in Ansible Vault (`docker_login` with `no_log: true` to avoid leaking secrets).
  - Pull the configured image and tag from Docker Hub (`docker_image`).
  - Attempt to stop any existing container with the same name (errors are ignored on first deploy).
  - Remove any previous container with the same name to avoid conflicting state.
  - Run the container with a stable name, port mapping `5000:5000`, restart policy, and optional environment variables.
  - Wait for the application port to become available on the target host.
  - Call the `/health` HTTP endpoint and assert HTTP 200 to verify the deployment.
- **Variables (from Vault / group vars):**
  - `dockerhub_username` — Docker Hub username.
  - `dockerhub_password` — Docker Hub personal access token.
  - `app_name` — logical application name, also used as the container name.
  - `docker_image` — full image name, e.g. `mararokkel/devops-info-service`.
  - `docker_image_tag` — image tag, `arm64` in this deployment.
  - `app_port` — container and host port, `5000`.
  - `app_container_name` — container name (`devops-info-service`).
- **Variables (defaults):**
  - `app_restart_policy` — Docker restart policy, `unless-stopped`.
  - `app_env` — optional environment variables for the container (empty map by default).
- **Handlers:**
  - `restart app container` — restarts the existing application container using `docker restart` when notified.
- **Dependencies:** expects Docker to be installed and running (i.e. `docker` role has completed successfully).

## 3. Idempotency Demonstration

Provisioning was executed twice using the same `playbooks/provision.yml` playbook.

- **First run (provision.yml):**
  - `common` role:
    - removed the broken HashiCorp APT source file;
    - updated the APT cache (after several retries due to the invalid HashiCorp repo);
    - installed all `common_packages`;
    - detected the current timezone and changed it to the configured value.
  - `docker` role:
    - installed Docker prerequisites;
    - configured the Docker APT repository and keyring;
    - installed Docker CE packages;
    - enabled and started the Docker service;
    - added user `maria` to the `docker` group;
    - installed `python3-docker`.
  - The final recap showed `changed` for system setup and Docker configuration tasks, as expected for the initial provisioning.

- **Second run (provision.yml):**
  - APT cache was already up to date, packages were installed, timezone matched the configured value, the Docker repository and keyring were present, Docker CE packages were installed, and the service was already running.
  - All tasks reported `ok` with **`changed=0`** in the play recap, and the timezone task was skipped because the current timezone matched the target value.

- **Why the roles are idempotent:**
  - Package installation uses `state: present`, so packages are only installed when missing.
  - The timezone is only changed when `timedatectl` reports a different value.
  - The Docker APT repository and keyring tasks use declarative modules (`apt_repository`, `file`, `get_url`), which only make changes when the configuration actually differs.
  - Group membership is managed with `append: yes`, so re‑running the play does not duplicate or remove users from other groups.
  - Systemd service management uses `state: started` and `enabled: yes`, which become no‑ops when Docker is already running and enabled.

## 4. Ansible Vault Usage

- **What is encrypted:**
  - Docker Hub credentials and application‑specific configuration are stored in `group_vars/all.yml`, which is encrypted with Ansible Vault (`ansible-vault create group_vars/all.yml`).
  - The file contains values such as:

    ```yaml
    dockerhub_username: mararokkel
    dockerhub_password: <Docker Hub personal access token>
    app_name: devops-info-service
    docker_image: "{{ dockerhub_username }}/{{ app_name }}"
    docker_image_tag: arm64
    app_port: 5000
    app_container_name: "{{ app_name }}"
    ```

- **How it is used:**
  - Playbooks are executed with `--ask-vault-pass`, and the deploy playbook explicitly includes the Vault file via `vars_files: ../group_vars/all.yml` in `playbooks/deploy.yml`.
  - The `app_deploy` role reads `dockerhub_username` and `dockerhub_password` to perform `docker_login`, and uses the image variables to pull and run the correct container.
  - Tasks that handle credentials are marked with `no_log: true`, so secrets do not appear in Ansible output or logs.

- **Vault password handling:**
  - Vault password is supplied interactively for this lab (`--ask-vault-pass`).
  - `.vault_pass` is explicitly ignored in `.gitignore` to prevent committing any local password files.
  - Only the encrypted Vault file is committed to Git; no plaintext secret files are tracked.

- **Why Vault is important:**
  - It allows Docker Hub tokens and other secrets to live in version control without exposing them in plaintext.
  - Multiple environments can share the same playbooks and roles while keeping different credentials encrypted with different Vault passwords.
  - Combined with `no_log: true`, Vault ensures that secrets are not printed to CI logs or shared accidentally during troubleshooting.

## 5. Deployment Verification

Application deployment was executed with:

```bash
ansible-playbook playbooks/deploy.yml --ask-become-pass --ask-vault-pass
```

Key parts of the output:

- **Docker Hub login and image pull:**
  - `app_deploy : Log in to Docker Hub` → `ok`
  - `app_deploy : Pull Docker image` → `changed`, pulling `mararokkel/devops-info-service:arm64` onto the Ubuntu VM.

- **Container lifecycle:**
  - On the first run, an attempt to stop a non‑existent container produced a handled error (`Cannot create container when image is not specified!`), which was ignored as expected.
  - `app_deploy : Remove old container if exists` → `ok`.
  - `app_deploy : Run application container` → `changed`, starting the container with name `devops-info-service` and port mapping `0.0.0.0:5000->5000/tcp`.

- **Runtime verification via Ansible:**

  Running:

  ```bash
  ansible webservers -a "docker ps" --ask-become-pass --ask-vault-pass
  ```

  produced:

  ```text
  CONTAINER ID   IMAGE                                  COMMAND           PORTS                    NAMES
  fd99fbbef119   mararokkel/devops-info-service:arm64   "python app.py"   0.0.0.0:5000->5000/tcp   devops-info-service
  ```

- **HTTP health checks from the control node:**

  ```bash
  curl http://192.168.64.6:5000/health
  ```

  returned:

  ```json
  {"status":"healthy","timestamp":"2026-02-24T08:03:38.148803+00:00","uptime_seconds":248}
  ```

  and:

  ```bash
  curl http://192.168.64.6:5000/
  ```

  returned a JSON document describing the service, including:
  - service name `devops-info-service` and version `1.0.0`;
  - available endpoints (`/` and `/health`);
  - runtime information (uptime, current time, timezone `UTC`);
  - system details (architecture `aarch64`, kernel version, Python version).

Together these outputs confirm that the container is running on the VM, the port is exposed correctly, and the application responds successfully on both the health endpoint and the main endpoint.

## 6. Key Decisions

- **Why use roles instead of plain playbooks:** separating `common`, `docker`, and `app_deploy` into roles keeps each concern focused and testable. Playbooks become thin orchestration layers that can be combined in different ways (for example, a full site deploy versus provisioning only).

- **How roles improve reusability:** roles are parameterised through defaults and group variables, so the same `common` and `docker` roles can be re‑used for other labs or projects by only changing inventory and variables, without touching task logic.

- **What makes a task idempotent:** it checks the existing state and only performs work if something is missing or different (for example, `state: present` for packages, conditional timezone changes, `state: started` for services, and `docker_container` with a fixed name and configuration). Re‑running the same play does not cause further changes when the system already matches the desired state.

- **How handlers improve efficiency:** handlers run only when notified by tasks that actually changed something (for example, after Docker packages or its repository configuration change). This avoids unnecessary restarts of services and keeps playbook output cleaner.

- **Why Ansible Vault is necessary:** it allows storing Docker Hub access tokens and other secrets alongside playbooks in Git without exposing them in plaintext, while still making them available to roles at runtime through a controlled decryption mechanism.

## 7. Challenges

- **Broken third‑party APT repository:** the VM had an outdated HashiCorp APT entry that caused `apt update` to fail. The `common` role explicitly removes the HashiCorp list file before refreshing the cache.
- **Deprecation of `apt-key` on newer Ubuntu:** the original Docker role used `apt_key`, which is no longer available; the role was updated to use `/etc/apt/keyrings` and `signed-by=` in the Docker APT repo definition.
- **Unsupported Ubuntu release for Docker CE:** the VM is running Ubuntu 25.04 (end‑of‑life), while Docker CE officially supports stable LTS releases. The role derives a supported codename (for example, `noble`) for the Docker repository to ensure package availability.
- **Architecture mismatch for Docker images:** Docker Hub initially only had `amd64` images, while the VM is `arm64`. A new `arm64` image for `mararokkel/devops-info-service` was built on the control node and pushed to Docker Hub, and the deploy role was configured to use the `arm64` tag.
- **SSH and sudo configuration for Ansible:** password‑based SSH was used initially, then SSH keys were added for convenience; `--ask-become-pass` is used so Ansible can run privileged tasks with `sudo` without hard‑coding passwords anywhere in configuration.
