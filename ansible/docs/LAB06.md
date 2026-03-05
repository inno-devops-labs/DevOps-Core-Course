# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Your Name  
**Date:** YYYY-MM-DD  
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

- **Roles updated:** `common`, `docker`, `provision.yml`, `site.yml`.
- **Block usage:**
  - `common`:
    - Packages block (`Manage common packages`) groups apt cache update and common package installation, with `rescue` running `apt-get update --fix-missing` and retrying `apt` on failure, and `always` touching `/tmp/common_packages_done`.
    - Users block (`Manage common users`) loops over `common_users` and manages Unix users, with `always` touching `/tmp/common_users_done`.
  - `docker`:
    - Install block (`Install Docker packages and dependencies`) installs Docker dependencies, repository, Docker Engine packages and `python3-docker`.
    - Config block (`Configure Docker key, service, and user`) manages keyrings directory, Docker GPG key, Docker service, and docker group membership, with `rescue` that waits 10 seconds and retries key and service, and `always` ensuring the service is enabled and started.
- **Tag strategy:**
  - Role-level in playbooks:
    - `common` role tagged with `common`.
    - `docker` role tagged with `docker`.
  - Within roles:
    - `common` role:
      - Packages block tagged: `common`, `packages`.
      - Users block tagged: `common`, `users`.
      - Timezone task tagged: `common`.
    - `docker` role:
      - Install block tagged: `docker`, `docker_install`, `packages`.
      - Config block tagged: `docker`, `docker_config`.
- **Selective execution examples (generate terminal output yourself):**
  - Run only Docker-related tasks:
    ```bash
    ansible-playbook playbooks/provision.yml --tags "docker"
    ```
    Expected output: only `docker` role tasks run; `common` role is skipped.
  - Skip `common` role:
    ```bash
    ansible-playbook playbooks/provision.yml --skip-tags "common"
    ```
    Expected output: `docker` tasks run, `common` tasks all reported as skipped.
  - Install packages only across roles:
    ```bash
    ansible-playbook playbooks/provision.yml --tags "packages"
    ```
    Expected output: `common` package block and `docker` install block run; timezone and user tasks are skipped.
  - Check mode:
    ```bash
    ansible-playbook playbooks/provision.yml --tags "docker" --check
    ```
    Expected output: `docker` tasks are shown as “would change” without modifying system state.
- **Error handling evidence (describe based on a failing run):**
  - Simulated failure: if `apt` cache update fails, Ansible enters the `rescue` block in `common`, runs `apt-get update --fix-missing`, retries the `apt` update, and then logs completion via the `always` block.
  - Note for screenshots: **take a screenshot of a run where the `rescue` block is triggered and include it here.**
- **Research answers:**
  - **What happens if rescue block also fails?**  
    The play fails at the first failing task inside `rescue`. Ansible does not attempt `always` tasks in `rescue`, but the outer `always` section of the original block still runs, ensuring cleanup/logging even when rescue cannot recover.
  - **Can you have nested blocks?**  
    Yes. Blocks can be nested to structure complex logic (for example, a top-level block for “Docker setup” with inner blocks for “packages” and “configuration”), but readability and tag inheritance should be considered carefully.
  - **How do tags inherit to tasks within blocks?**  
    Tags declared on the block are inherited by all tasks inside the block. Tasks can add their own tags, and the effective tag set is the union of the block tags and task tags.

---

## Task 2: Docker Compose (3 pts)

### Implementation

- **Role rename:**
  - Previous role: `app_deploy`.
  - New role: `web_app` (new directory under `ansible/roles/web_app`).
  - Playbook updates:
    - `playbooks/deploy.yml` now uses:
      ```yaml
      roles:
        - role: web_app
          tags:
            - web_app
            - app_deploy
      ```
    - `playbooks/site.yml` includes `web_app` with the same tags.
- **Docker Compose template:**
  - File: `roles/web_app/templates/docker-compose.yml.j2`.
  - Structure:
    ```yaml
    version: '{{ docker_compose_version }}'

    services:
      {{ app_name }}:
        image: {{ docker_image }}:{{ docker_tag | default('latest') }}
        container_name: {{ app_name }}
        ports:
          - "{{ app_port }}:{{ app_internal_port | default(app_port) }}"
        environment:
    {% for key, value in (app_env | default({})).items() %}
          {{ key }}: {{ value }}
    {% endfor %}
        restart: {{ app_restart_policy }}
        networks:
          - web_app_net

    networks:
      web_app_net:
        driver: bridge
    ```
  - Variables used:
    - `app_name` — service/container name.
    - `docker_image` — full image name, typically `{{ dockerhub_username }}/{{ app_name }}`.
    - `docker_tag` — version tag, defaulting to `docker_image_tag` or `latest`.
    - `app_port` — host port (default `8000` in role defaults).
    - `app_internal_port` — container port (defaults to `app_port`).
    - `docker_compose_version` — top-level Compose version, default `"3.8"`.
    - `app_env` — dictionary of environment variables.
    - `app_restart_policy` — restart policy (default `unless-stopped`).
- **Role dependencies:**
  - File: `roles/web_app/meta/main.yml`:
    ```yaml
    ---
    dependencies:
      - role: docker
    ```
  - This ensures the `docker` role is run before `web_app`, so Docker Engine and the Compose plugin are available before deploying the app.
- **Deployment tasks:**
  - File: `roles/web_app/tasks/main.yml`:
    - Includes wipe logic first (see Task 3).
    - Deployment block:
      - Ensures `compose_project_dir` exists (default `/opt/{{ app_name }}`).
      - Templates `docker-compose.yml` to `{{ compose_project_dir }}/docker-compose.yml`.
      - Uses `community.docker.docker_compose_v2` with:
        - `project_src: "{{ compose_project_dir }}"`
        - `state: present`
        - `pull: true`
      - Registers `web_app_compose_result`.
      - `rescue` block logs a structured error message if deployment fails.
    - Tagged with `app_deploy` and `compose`.

### Variables

- **Defaults (role-level):**
  - File: `roles/web_app/defaults/main.yml`:
    - `app_name: devops-app`
    - `app_port: 8000`
    - `app_internal_port: 8000`
    - `docker_image: ""` (provided via `group_vars/all.yml` in real runs).
    - `docker_tag: "{{ docker_image_tag | default('latest') }}"`
    - `compose_project_dir: "/opt/{{ app_name }}"`
    - `docker_compose_version: "3.8"`
    - `app_health_path: /health`
    - `app_restart_policy: unless-stopped`
    - `app_env: {}`
    - `web_app_wipe: false`
- **Group variables example:**
  - File: `ansible/group_vars/all.yml.example` extended with:
    ```yaml
    app_internal_port: "{{ app_port }}"
    compose_project_dir: "/opt/{{ app_name }}"
    docker_compose_version: "3.8"
    app_env: {}
    ```

### Testing & Evidence

- **Deployment run (simulated):**
  - Command:
    ```bash
    ansible-playbook playbooks/deploy.yml
    ```
  - Expected behavior:
    - `web_app` role runs, creates `/opt/devops-app`, templated `docker-compose.yml`, and uses Docker Compose v2 to start the stack.
    - Subsequent runs are idempotent: `docker_compose_v2` reports `ok` with no changes if nothing changed in the template or variables.
- **Idempotency proof (describe based on two runs):**
  - First run: several tasks report `changed`, and containers are created.
  - Second run: same playbook shows `ok=...`, `changed=0`, demonstrating idempotent deployment.
- **Application verification (simulated):**
  - On the VM:
    ```bash
    docker ps
    docker compose -f /opt/devops-app/docker-compose.yml ps
    curl http://localhost:8000/
    curl http://localhost:8000/health
    ```
  - Note for screenshots: **take a screenshot of `docker ps` and the curl output showing the app responding.**

### Research answers

- **`restart: always` vs `restart: unless-stopped`:**  
  `always` restarts the container on all exits including when Docker itself restarts, even if you manually stopped it. `unless-stopped` restarts the container on failures and daemon restarts, but respects an explicit manual stop and will not restart it automatically after that.
- **Docker Compose networks vs Docker bridge networks:**  
  Compose-defined networks create dedicated, named networks per project with built-in service name DNS resolution and clearer isolation. The default Docker bridge network is shared across many containers, can get crowded, and does not provide project-level scoping by default.
- **Referencing Ansible Vault variables in the template:**  
  Vault only encrypts how values are stored; at runtime, decrypted variables behave like normal variables. As long as Vault-encrypted values (for example, `app_secret_key`) are defined, they can be used directly in the Jinja2 template (for example, under `environment:`) exactly like regular variables.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

- **Control variable:**
  - `web_app_wipe` defined in `roles/web_app/defaults/main.yml` as `false`.
- **Wipe tasks file:**
  - File: `roles/web_app/tasks/wipe.yml`:
    - Uses a block `Wipe web application` with:
      - `community.docker.docker_compose_v2` with `state: absent` to stop and remove containers for the project at `compose_project_dir`.
      - Removal of `{{ compose_project_dir }}/docker-compose.yml`.
      - Removal of the application directory `{{ compose_project_dir }}`.
      - Final `debug` message confirming wipe completion.
    - `ignore_errors: true` used on destructive tasks so that rerunning on an already-clean system does not fail the play.
    - The entire block is guarded by:
      ```yaml
      when: web_app_wipe | bool
      tags:
        - web_app_wipe
      ```
- **Include in main tasks:**
  - `roles/web_app/tasks/main.yml` starts with:
    ```yaml
    - name: Include wipe tasks
      ansible.builtin.include_tasks: wipe.yml
      tags:
        - web_app_wipe
    ```
  - This ensures wipe runs before deployment tasks when both are requested.

### Test scenarios (described)

Use `ansible-playbook playbooks/deploy.yml` with different combinations of tags and extra vars.

- **Scenario 1: Normal deployment (wipe should NOT run)**
  - Command:
    ```bash
    ansible-playbook playbooks/deploy.yml
    ```
  - Behavior: `web_app_wipe` remains `false` (default), so `wipe.yml` is included but tasks are skipped due to `when`. Only deployment block runs, app stays (or becomes) deployed.
- **Scenario 2: Wipe only**
  - Command:
    ```bash
    ansible-playbook playbooks/deploy.yml \
      -e "web_app_wipe=true" \
      --tags web_app_wipe
    ```
  - Behavior: Only tagged wipe tasks run; deployment block (tagged `app_deploy`, `compose`) does not run. The app is removed, directories cleaned up.
- **Scenario 3: Clean reinstallation (wipe → deploy)**
  - Command:
    ```bash
    ansible-playbook playbooks/deploy.yml \
      -e "web_app_wipe=true"
    ```
  - Behavior:
    - `wipe.yml` block runs first (because of `include_tasks` at the top).
    - Deployment block runs second, recreating directory, templating Compose file, and starting containers.
- **Scenario 4: Safety checks**
  - Command:
    ```bash
    ansible-playbook playbooks/deploy.yml --tags web_app_wipe
    ```
  - Behavior: Tag is present, but `web_app_wipe` is still `false`, so `when` condition prevents any wipe task from running; deployment runs normally.

> Note for screenshots: **capture terminal output for each scenario (1–4) showing which tasks were run/skipped and include them here.**

### Research answers

1. **Why use both variable AND tag?**  
   Using both a variable and a tag is a double-safety mechanism. The tag ensures wipe logic is never accidentally triggered by a generic playbook run, and the boolean variable ensures that even when the tag is used, wipes only happen when the operator explicitly sets `web_app_wipe=true`.
2. **Difference between `never` tag and this approach?**  
   The `never` tag completely prevents tasks from running unless `--tags never` is explicitly specified, which is easy to forget or misuse. The variable+tag approach allows you to keep wipe tasks visible and testable, but still gated behind an explicit variable, supporting combined flows like “wipe then deploy” without special tags like `never`.
3. **Why must wipe logic come BEFORE deployment in main.yml?**  
   Placing wipe logic first enables clean reinstallations (`wipe → deploy`) in a single playbook run and prevents newly deployed containers from being wiped right after deployment.
4. **When would you want clean reinstallation vs. rolling update?**  
   Clean reinstallations are useful when state must be fully reset (for example, corrupted volumes, incompatible schema changes). Rolling updates are preferable for minimizing downtime and preserving state, typically in multi-instance setups where you can update one instance at a time.
5. **How to extend this to wipe Docker images and volumes too?**  
   Additional tasks could call `community.docker.docker_image` with `state: absent` for specific images and `community.docker.docker_volume` with `state: absent` for named volumes, still guarded by `web_app_wipe | bool` and possibly an extra variable such as `web_app_wipe_volumes`.

---

## Task 4: CI/CD (3 pts)

### Workflow Setup

- **Workflow file:** `.github/workflows/ansible-deploy.yml`.
- **Triggers:**
  - On `push` to `main` or `master` when:
    - Files under `ansible/**` change, or
    - The workflow file itself changes.
  - On `pull_request` to `main` or `master` with changes under `ansible/**`.
- **Jobs:**
  - `lint`:
    - Runs on `ubuntu-latest`.
    - Checks out code.
    - Sets up Python 3.12.
    - Installs `ansible`, `ansible-lint`, `docker` Python package, and Ansible collections from `ansible/requirements.yml`.
    - Runs `ansible-lint` against all playbooks in `ansible/playbooks/*.yml`.
  - `deploy`:
    - Depends on `lint`.
    - Runs on `ubuntu-latest`.
    - Checks out code and sets up Python 3.12.
    - Installs `ansible`, `docker`, and required collections.
    - Sets up SSH using:
      - `SSH_PRIVATE_KEY` for the private key.
      - `VM_HOST` for known_hosts population.
    - Deploys using:
      ```bash
      cd ansible
      echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
      ansible-playbook playbooks/deploy.yml \
        -i inventory/hosts.ini \
        --vault-password-file /tmp/vault_pass \
        --tags "app_deploy"
      rm /tmp/vault_pass
      ```
    - Verifies deployment with:
      ```bash
      curl -f http://${{ secrets.VM_HOST }}:8000
      curl -f http://${{ secrets.VM_HOST }}:8000/health
      ```

### GitHub Secrets

- Required secrets (configured in “Settings → Secrets and variables → Actions”):
  - `ANSIBLE_VAULT_PASSWORD` — used to decrypt `group_vars/all.yml`.
  - `SSH_PRIVATE_KEY` — private key that matches the public key configured on the VM.
  - `VM_HOST` — public IP / DNS of the VM (for example `54.208.22.101`).
  - `VM_USER` — SSH username (not used directly in this sample, but typically used in inventory or SSH configuration).
- Vault password handling:
  - The workflow writes the vault password to `/tmp/vault_pass`, passes `--vault-password-file` to `ansible-playbook`, and deletes the temporary file afterwards.

### Evidence (describe)

- **Successful lint run:**
  - In GitHub Actions, the `Ansible Lint` job completes successfully (green check), showing `ansible-lint` output with no errors.
- **Successful deployment run:**
  - The `Deploy Application` job shows `ansible-playbook` output where:
    - `web_app` role runs.
    - Docker Compose deployment tasks report `changed` or `ok`.
  - The final `Verify Deployment` step exits with status 0 and prints the app’s HTTP response.
- **Status badge (to add manually):**
  - Add in `README.md` or `ansible/README.md`:
    ```markdown
    [![Ansible Deployment](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml)
    ```
  - Note for screenshots: **take a screenshot of a successful workflow run in the GitHub Actions UI and include it here.**

### Research answers

1. **Security implications of storing SSH keys in GitHub Secrets:**  
   GitHub Secrets are encrypted at rest and redacted in logs, but anyone with write access to the repo can modify workflows to exfiltrate them. It is important to restrict repository access, rotate keys regularly, scope keys to specific hosts, and avoid reusing them outside CI/CD.
2. **Staging → production deployment pipeline:**  
   A common pattern is to have two environments with separate inventories or variable files. Workflows can deploy first to staging on every push, then promote to production only after manual approval steps or when tagging a release (for example, by using `workflow_run` triggers or `environment` protection rules with required reviewers).
3. **Making rollbacks possible:**  
   Store previous docker image tags (or Compose configurations) and keep deployments declarative. CI/CD can support rollbacks by allowing you to re-run deployment with a previous tag or configuration, or by maintaining a history of artifacts and using blue/green or canary strategies to flip traffic back quickly.
4. **Self-hosted runner vs GitHub-hosted security:**  
   Self-hosted runners live inside your infrastructure, so secrets never leave your network and runners can reach private resources directly. However, they must be maintained, patched, and locked down. GitHub-hosted runners are ephemeral and maintained by GitHub, but act as external machines that must reach your infrastructure over the public internet via SSH or VPN.

---

## Task 5: Documentation

This `ansible/docs/LAB06.md` file serves as the main documentation for Lab 6 and includes:

- Overview of changes to Ansible roles (`common`, `docker`, `web_app`) and playbooks.
- Explanation of the block and tag strategy, Docker Compose migration, wipe logic, and CI/CD workflow.
- Described test runs and expected outputs for:
  - Tagged execution (`--tags` / `--skip-tags`).
  - Docker Compose deployments and idempotency.
  - Wipe scenarios.
  - CI/CD runs and verification.
- Research question answers for each task.

Add your own:

- Actual command outputs from your VM runs.
- Screenshots for:
  - Rescue block execution.
  - `docker ps` and curl verification.
  - Wipe scenarios.
  - GitHub Actions successful workflow runs and status badge.

---

## Bonus Parts

Bonus parts (multi-app deployment and multi-app CI/CD) are **not implemented** in this submission. They could be added later by:

- Reusing the `web_app` role with different variable files and ports.
- Adding dedicated playbooks (`deploy_python.yml`, `deploy_bonus.yml`, `deploy_all.yml`).
- Creating additional CI/CD workflows or a matrix-based workflow targeting each app independently.

---

## Summary

- Implemented Ansible blocks, tags, and error handling for `common` and `docker` roles with clear tag strategy.
- Migrated application deployment to a new `web_app` role using Docker Compose v2, with role dependencies and idempotent deployment.
- Added safe, double-gated wipe logic with `web_app_wipe` variable + tag and integrated it before deployment in the main tasks.
- Created an Ansible CI/CD GitHub Actions workflow with linting, deployment, and HTTP-based verification, and documented behavior and security considerations.

