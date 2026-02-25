## Lab 5 — Ansible Fundamentals (Implementation Notes)

---

### 1. Architecture Overview

- **Ansible version used**
  - Example format:
    ```bash
    $ ansible --version
    ansible [core 2.18.12]
    config file = /home/alex/courses/DevOps-Core-Course/ansible/ansible.cfg
    configured module search path = ['/home/alex/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
    ansible python module location = /usr/lib/python3.14/site-packages/ansible
    ansible collection location = /home/alex/.ansible/collections:/usr/share/ansible/collections
    executable location = /usr/bin/ansible
    python version = 3.14.2 (main, Dec  5 2025, 00:00:00) [GCC 15.2.1 20251111 (Red Hat 15.2.1-4)] (/usr/bin/python3)
    jinja version = 3.1.6
    libyaml = True
    ```
- **Target VM OS and version**
  - Ubuntu 22.04 LTS or 24.04 LTS.
- **Role structure (what we implemented)**
  - `roles/common`: base system provisioning (apt cache, common packages, timezone).
  - `roles/docker`: Docker engine installation and configuration.
  - `roles/app_deploy`: deployment of your Dockerized Python app from Docker Hub.
  - `playbooks/provision.yml`: applies `common` and `docker` to `webservers` group.
  - `playbooks/deploy.yml`: applies `app_deploy` to `webservers` group.
  - `playbooks/site.yml`: convenience entrypoint importing both provision and deploy playbooks.
- **Why roles instead of monolithic playbooks?**
  - Roles keep concerns separated (system prep, Docker, app deployment).
  - They are reusable across future labs or other projects.
  - They are easier to test and maintain than one large playbook.

---

### 2. Roles Documentation

#### 2.1 `common` role

- **Purpose**
  - Prepare any Ubuntu host with essential tools and a consistent timezone.
- **Key variables (from `roles/common/defaults/main.yml`)**
  - `common_packages`: list of common packages installed on all hosts (e.g. `python3-pip`, `curl`, `git`, `vim`, `htop`, `ca-certificates`, `gnupg`, `lsb-release`).
  - `common_timezone`: default system timezone (currently `"Etc/UTC"`).
- **Handlers**
  - None in this role (all tasks are self‑contained and idempotent).
- **Notes**
  - The timezone task uses `community.general.timezone`, so you may need:
    ```bash
    ansible-galaxy collection install community.general
    ```

#### 2.2 `docker` role

- **Purpose**
  - Install and configure Docker CE from the official Docker APT repository and ensure it is ready for Ansible’s Docker modules.
- **Key variables (from `roles/docker/defaults/main.yml`)**
  - `docker_apt_arch`: architecture for the APT repo (`"amd64"` by default).
  - `docker_apt_repo`: full Docker APT repository line, using `{{ ansible_distribution_release }}`.
  - `docker_packages`: core Docker packages (`docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`).
  - `docker_service_name`: service name to manage (`"docker"`).
  - `docker_user`: user added to the `docker` group (defaults to `{{ ansible_user | default('ubuntu') }}`).
  - `docker_python_packages`: Python packages needed for Docker modules (`python3-docker`).
- **Handlers (from `roles/docker/handlers/main.yml`)**
  - `restart docker`: restarts the Docker service when the GPG key or APT repository changes.
- **Dependencies**
  - Uses `apt`, `apt_key`, `apt_repository`, `service`, `user` modules (all built‑in).

#### 2.3 `app_deploy` role

- **Purpose**
  - Log into Docker Hub with vaulted credentials, pull your application image, run the container, and verify the app is healthy.
- **Key variables (from `roles/app_deploy/defaults/main.yml` and vaulted vars)**
  - `app_name`: logical name of the app (`"devops-app"`).
  - `app_port`: internal and external port (`5000` by default).
  - `app_container_name`: container name (defaults to `{{ app_name }}`).
  - `app_restart_policy`: Docker restart policy (`"unless-stopped"`).
  - `app_env`: map of environment variables (defaults to `{}`).
  - `app_healthcheck_path`: HTTP path for health checking (`"/health"`).
  - `docker_image`: image name built from vaulted `dockerhub_username` and `app_name`.
  - `docker_image_tag`: tag to deploy (`"latest"`).
  - **From `group_vars/all.yml` (vault encrypted; you must create it):**
    - `dockerhub_username`: your Docker Hub username.
    - `dockerhub_password`: your Docker Hub access token or password.
- **Handlers (from `roles/app_deploy/handlers/main.yml`)**
  - `restart application container`: restarts the app container using the Docker container module.
- **Dependencies**
  - Uses the `community.docker` collection (`docker_login`, `docker_image`, `docker_container`) and built‑in `wait_for` and `uri`.
  - TODO: install the collection on your control node:
    ```bash
    ansible-galaxy collection install community.docker
    ```

---

### 3. Idempotency Demonstration

1. **First run of `provision.yml`**
  - Command to run from the `ansible/` directory:
  ---

< PLAY [Provision web servers] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

---

< TASK [Gathering Facts] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

[WARNING]: Platform linux on host alex-devops-vm is using the discovered Python interpreter at
/usr/bin/python3.12, but future installation of another Python interpreter could change the meaning of that
path. See [https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html](https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html) for
more information.
ok: [alex-devops-vm]

---

< TASK [common : Ensure apt cache is up to date] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [common : Install common packages] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [common : Set system timezone] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Install prerequisites for Docker] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add Docker official GPG key] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add Docker APT repository] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Install Docker packages] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

## ok: [alex-devops-vm]
 _____________________________________________________
/ TASK [docker : Ensure Docker service is enabled and   
\ running]                                            /

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add user to docker group] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

## ok: [alex-devops-vm]
 __________________________________________________________
/ TASK [docker : Install Python Docker package for Ansible   
\ modules]                                                 /

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< PLAY RECAP >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

alex-devops-vm             : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   

```
 ```
```

1. **Second run of `provision.yml`**
  - Run the same command again:
    ---

< PLAY [Provision web servers] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

---

< TASK [Gathering Facts] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

[WARNING]: Platform linux on host alex-devops-vm is using the discovered Python interpreter at
/usr/bin/python3.12, but future installation of another Python interpreter could change the meaning of that
path. See [https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html](https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html) for
more information.
ok: [alex-devops-vm]

---

< TASK [common : Ensure apt cache is up to date] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [common : Install common packages] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [common : Set system timezone] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Install prerequisites for Docker] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add Docker official GPG key] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add Docker APT repository] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Install Docker packages] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

## ok: [alex-devops-vm]
 _____________________________________________________
/ TASK [docker : Ensure Docker service is enabled and   
\ running]                                            /

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [docker : Add user to docker group] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

## ok: [alex-devops-vm]
 __________________________________________________________
/ TASK [docker : Install Python Docker package for Ansible   
\ modules]                                                 /

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< PLAY RECAP >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

alex-devops-vm             : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0  
     ```bash

```
 ```
```

1. **Analysis**
  - TODO: briefly answer:
    - Which tasks showed `changed` on the first run and why? (e.g. installing packages, adding repo, first Docker setup).
    - Why do most or all tasks show `ok` on the second run? Relate this to idempotent modules like `apt`, `service`, and `user`.

---

### 4. Ansible Vault Usage

This section describes how you securely store Docker Hub credentials and app settings.

- **Vault file location**
  - We expect an encrypted file at: `ansible/group_vars/all.yml`.
- **How to create it (you must do this manually)**
  - From inside the `ansible/` directory:
    ```bash
    ansible-vault create group_vars/all.yml
    ```
  - When the editor opens, add content similar to:
    ```yaml
    ---
    # Docker Hub credentials
    dockerhub_username: your-username
    dockerhub_password: your-access-token

    # Application configuration
    app_name: devops-app
    docker_image: "{{ dockerhub_username }}/{{ app_name }}"
    docker_image_tag: latest
    app_port: 5000
    app_container_name: "{{ app_name }}"
    ```
  - Save and exit; Ansible will store this file **encrypted**.
- **Vault password management strategy**
  - Recommended approach:
    ```bash
    echo "your-strong-vault-password" > .vault_pass
    chmod 600 .vault_pass
    ```
  - Then either:
    - Pass `--vault-password-file .vault_pass` on the CLI, **or**
    - Add this to `ansible/ansible.cfg` (already prepared with a commented line) and keep `.vault_pass` out of git.
- **Example of encrypted file**
  - TODO: show a small snippet of `group_vars/all.yml` as seen on disk (do **not** decrypt it, just `cat` it) to prove it is encrypted:
    ```bash
    $ cat group_vars/all.yml
    ```
- **Why Ansible Vault is important**
  - It allows you to commit configuration that references secrets without exposing the actual secret values.
  - It keeps credentials out of plain text files and source control history.

---

### 5. Deployment Verification

You must deploy the application and capture verification output here.

1. **Run the deployment playbook**
  - From the `ansible/` directory:
  ---

< PLAY [Deploy application] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

---

< TASK [Gathering Facts] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

[WARNING]: Platform linux on host alex-devops-vm is using the discovered Python interpreter at
/usr/bin/python3.12, but future installation of another Python interpreter could change the meaning of that
path. See [https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html](https://docs.ansible.com/ansible-core/2.18/reference_appendices/interpreter_discovery.html) for
more information.
ok: [alex-devops-vm]

---

< TASK [app_deploy : Log in to Docker Hub] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [app_deploy : Pull application image] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [app_deploy : Ensure application container is running] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [app_deploy : Wait for application port to be open] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< TASK [app_deploy : Verify health endpoint] >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

ok: [alex-devops-vm]

---

< PLAY RECAP >

---

```
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
```

alex-devops-vm             : ok=6    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0  
     ```

1. **Container status**
  - From your control node, using Ansible:
  - ```

  ```
   alex-devops-vm | CHANGED | rc=0 >>

CONTAINER ID   IMAGE                       COMMAND           CREATED          STATUS                    PORTS                    NAMES
9b422b21cc35   tbyf217/devops-app:latest   "python app.py"   10 minutes ago   Up 10 minutes (healthy)   0.0.0.0:5000->5000/tcp   devops-app

   - 

1. **Handler execution**
  - If you change something that triggers the `restart application container` handler (for example, image tag or environment), Ansible should show `RUNNING HANDLER` in the output.
  - TODO: if you see handlers run, note when and why here.

---

### 6. Key Decisions

Brief answers (2–3 sentences each).

- **Why use roles instead of plain playbooks?**
  - Roles enforce a clean separation of concerns (system prep vs Docker vs app deployment) and make it easy to reuse the same logic across environments and future labs.
  - They also keep playbooks very small and readable (`provision.yml` and `deploy.yml` simply list roles), which improves maintainability.
- **How do roles improve reusability?**
  - Each role encapsulates tasks, defaults, and handlers behind a clear interface (variables), so you can drop the role into another project with minimal changes.
  - Overrides can be done via inventory/group vars without editing the role code.
- **What makes a task idempotent?**
  - An idempotent task converges the system to a desired state using declarative modules (`state: present`, `state: started`) so rerunning it does not cause additional changes.
  - In Ansible, you see this as `ok` (no change) on subsequent runs when nothing in the desired state has changed.
- **How do handlers improve efficiency?**
  - Handlers run only when notified by tasks that actually changed something (e.g. repo or config changes), so services are restarted only when required.
  - This reduces unnecessary restarts and makes playbook runs faster and safer.
- **Why is Ansible Vault necessary?**
  - It allows you to keep secrets (like Docker Hub credentials) in version control without exposing them in plain text.
  - This is critical for real‑world automation where multiple people and systems interact with the same repository.

---

### 7. Challenges (Optional)

Use this section for any notes about issues you hit and how you solved them.

- TODO: add bullet points here if you encountered interesting problems (e.g. missing collections, SSH issues, Docker repo errors) and how you fixed them.

---

### Bonus (Optional) — Dynamic Inventory Notes

If you implement the bonus task with a cloud inventory plugin, document it here.

- **Cloud provider and plugin**
  - TODO: e.g. `amazon.aws.aws_ec2`, `google.gcp.gcp_compute`, `yandex.cloud.yandex_compute`, etc.
- **Inventory config file**
  - TODO: describe the YAML file you created under `ansible/inventory/` (name, key options like `plugin`, `regions`, `filters`, `compose`, and how you derive `ansible_host` and `ansible_user`).
- **Verification output**

}

```

- **Benefits compared to static inventory**
  - Briefly explain how dynamic inventory avoids manual IP updates when VMs are recreated or scaled.

```

