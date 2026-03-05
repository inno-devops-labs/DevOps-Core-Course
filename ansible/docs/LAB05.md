 # LAB05 — Ansible Fundamentals

 ## 1. Architecture Overview

 - **Ansible version:** _(fill after running `ansible --version`)_  
 - **Target VM:** Ubuntu 22.04/24.04 LTS from Lab 4  
 - **Structure:**
   - `ansible/ansible.cfg`
   - `ansible/inventory/hosts.ini`
   - `ansible/roles/common`, `docker`, `web_app` (renamed from app_deploy in Lab 6)
   - `ansible/playbooks/provision.yml`, `deploy.yml`, `site.yml`
   - `ansible/group_vars/all.yml` (vaulted; example in `all.yml.example`)

 Roles are used instead of monolithic playbooks for reusability, clarity, and easier testing.

 ## 2. Roles Documentation

 ### common
 - **Purpose:** Base system provisioning (apt cache, common packages, timezone).
 - **Variables:** `common_packages`, `common_timezone`.
 - **Handlers:** none.
 - **Dependencies:** none.

 ### docker
 - **Purpose:** Install and configure Docker Engine and dependencies.
 - **Variables:** `docker_packages`, `docker_user`.
 - **Handlers:** `restart docker`.
 - **Dependencies:** expects `docker_user` to exist (e.g. created outside or by another role).

 ### web_app (formerly app_deploy)
 - **Purpose:** Deploy app via Docker Compose; log in to Docker Hub, template compose file, run containers, verify health.
 - **Variables:** `app_name`, `app_port`, `app_container_name`, `app_restart_policy`, `app_environment`, plus vaulted `dockerhub_username`, `dockerhub_password`, `docker_image`, `docker_image_tag`.
 - **Handlers:** `restart app container`.
 - **Dependencies:** Docker installed and running (via `docker` role).

 ## 3. Idempotency Demonstration

 Paste and briefly annotate your outputs:

 - **First run of `playbooks/provision.yml`:** _(expect many `changed`)_  
 - **Second run of `playbooks/provision.yml`:** _(expect all `ok`, no `changed`)_  

 Explain which tasks changed on the first run and why nothing changed on the second run (desired state already reached).

 ## 4. Ansible Vault Usage

 - Sensitive values (Docker Hub credentials, image name) are stored in `group_vars/all.yml`, which **you create with `ansible-vault`** using the structure from `group_vars/all.yml.example`.
 - Use either `--ask-vault-pass` or a `.vault_pass` file (added to `.gitignore`) for automation.
 - Vault ensures credentials are encrypted at rest in Git.

 Show:
 - Example of encrypted `group_vars/all.yml` (header only; content unreadable).
 - How you manage the vault password.

 ## 5. Deployment Verification

 After running:

 ```bash
 ansible-playbook playbooks/deploy.yml --ask-vault-pass
 ```

 Capture:
 - `docker ps` on the VM showing the container running.
 - `curl http://<VM-IP>:5000/health` and `/` outputs.
 - Any handler executions (e.g., app restart).



