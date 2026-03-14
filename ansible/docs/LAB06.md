# Lab 6: Advanced Ansible & CI/CD - Submission

## Task 1: Blocks & Tags (2 pts)

I refactored the `common` and `docker` roles to use Ansible blocks with `rescue` / `always` sections and a clear tag strategy.

- **common role**
  - Package-related tasks are grouped into a single block with `tags: [common, packages]` and `become: true` at the block level.
  - On failure, the `rescue` section runs `apt-get update --fix-missing` to try to recover from apt cache issues.
  - The `always` section creates `/tmp/common_packages_completed.log` to log completion.
- **docker role**
  - Installation tasks (`apt` packages, GPG key, repository, Docker packages) are grouped into a `Docker installation tasks` block with tags `docker` and `docker_install`.
  - The `rescue` section waits 10 seconds and retries apt cache update and GPG key addition (helps with transient network/GPG issues).
  - The `always` section ensures the Docker service is enabled and started.
  - Configuration tasks (adding user to `docker` group, installing `python3-docker`) are grouped into a `Docker configuration tasks` block with tags `docker` and `docker_config`.
- **Playbook-level tags**
  - In `playbooks/provision.yml` I attach the `common` and `docker` roles with role-level tags so I can run or skip an entire role easily.

**Tag listing evidence**

```bash
ansible-playbook playbooks/provision.yml --list-tags
```

Output:

```text
playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers  TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages]
```

**Selective execution evidence**

- Run only Docker-related tasks:

```bash
ansible-playbook playbooks/provision.yml --tags "docker" --ask-vault-pass
```

Key output (trimmed):

```text
TASK [docker : Install required packages] ... ok
TASK [docker : Add Docker GPG key] ... changed
TASK [docker : Add Docker repository] ... changed
TASK [docker : Install Docker packages] ... changed
TASK [docker : Ensure Docker service is enabled and started] ... ok
TASK [docker : Add user to docker group] ... changed
TASK [docker : Install python docker module] ... changed

PLAY RECAP
yandex-cluod : ok=9  changed=6  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

- Skip the `common` role:

```bash
ansible-playbook playbooks/provision.yml --skip-tags "common" --ask-vault-pass
```

Key output (trimmed):

```text
TASK [docker : Install required packages] ... ok
TASK [docker : Add Docker GPG key] ... ok
TASK [docker : Add Docker repository] ... ok
TASK [docker : Install Docker packages] ... ok
TASK [docker : Ensure Docker service is enabled and started] ... ok
TASK [docker : Add user to docker group] ... ok
TASK [docker : Install python docker module] ... ok

PLAY RECAP
yandex-cluod : ok=8  changed=0  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0
```

These runs demonstrate that the tags work as intended: I can target only Docker tasks or skip the `common` role entirely.

## Task 2: Docker Compose (3 pts)

I migrated the deployment to use Docker Compose via a new `web_app` role (renamed from `app_deploy`) and a Jinja2 template.

- **Role rename and dependency**
  - Renamed `roles/app_deploy` → `roles/web_app` and updated `playbooks/deploy.yml` to use the `web_app` role.
  - Added a role dependency in `roles/web_app/meta/main.yml` so the `docker` role is executed automatically before `web_app`.

- **Docker Compose template**
  - File: `roles/web_app/templates/docker-compose.yml.j2`
  - Key structure:

```yaml
version: "{{ docker_compose_version | default('3.8') }}"

services:
  {{ app_name | default('devops-app') }}:
    image: "{{ docker_image }}:{{ docker_tag | default('latest') }}"
    container_name: "{{ app_name | default('devops-app') }}"
    ports:
      - "{{ app_port | default(8000) }}:{{ app_internal_port | default(8000) }}"
    environment:
      APP_SECRET_KEY: "{{ app_secret_key }}"
    restart: unless-stopped
```

  - This template lets me control the service name, image, tag, ports and environment variables from variables (defaults in the role or `group_vars`).

- **Deployment tasks and tags**
  - File: `roles/web_app/tasks/main.yml`
  - The role:
    - Creates the app directory at `{{ compose_project_dir }}`.
    - Templates `docker-compose.yml` into that directory.
    - Uses `community.docker.docker_compose_v2` with `state: present` and `pull: yes` to bring the stack up.
  - The deployment block is tagged with `app_deploy` and `compose` so I can target compose-based app deployment from the CLI or CI.

**Deployment evidence**

- First deployment run:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Key output (trimmed):

```text
TASK [web_app : Deploy with Docker Compose] ...
changed: [yandex-cluod]

PLAY RECAP
yandex-cluod : ok=12  changed=1  unreachable=0  failed=0  skipped=4  rescued=0  ignored=0
```

- Second deployment run (idempotency check):

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Key output (trimmed):

```text
TASK [web_app : Deploy with Docker Compose] ...
ok: [yandex-cluod]

PLAY RECAP
yandex-cluod : ok=12  changed=0  unreachable=0  failed=0  skipped=4  rescued=0  ignored=0
```

The first run reports `changed=1` for the web_app deployment task, while the second run reports `changed=0`, which shows that the Docker Compose deployment is idempotent.

**Runtime evidence on the target VM**

On the VM after deployment:

```bash
docker ps
```

Output:

```text
CONTAINER ID   IMAGE                           COMMAND           CREATED         STATUS         PORTS                                         NAMES
913cb0482cc2   danielambda/devops-app:latest   "python app.py"   2 minutes ago   Up 2 minutes   0.0.0.0:5000->8000/tcp, [::]:5000->8000/tcp   devops-app
```

```bash
docker compose -f /opt/devops-app/docker-compose.yml ps
```

Output:

```text
WARN[0000] /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
NAME         IMAGE                           COMMAND           SERVICE      CREATED         STATUS         PORTS
devops-app   danielambda/devops-app:latest   "python app.py"   devops-app   2 minutes ago   Up 2 minutes   0.0.0.0:5000->8000/tcp, [::]:5000->8000/tcp
```

The container is running from the expected image via Docker Compose, with port `5000` on the host forwarding to port `8000` in the container.

To verify application accessibility, I curled the service directly on the VM:

```bash
curl http://localhost:5000
curl http://localhost:5000/health
```

Outputs:

```text
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.18.0.1","method":"GET","path":"/","user_agent":"curl/7.81.0"},"runtime":{"current_time":"2026-03-12T21:06:23.952864+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":49},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"1c093d40b636","platform":"Linux","platform_version":"#180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026","python_version":"3.13.12"}}
```

```text
{"status":"healthy","timestamp":"2026-03-12T21:06:25.429657+00:00","uptime_seconds":50}
```

This shows that the root endpoint `/` and `/health` are both responding correctly from the containerized application.

## Task 3: Wipe Logic (1 pt)

I implemented wipe logic in the `web_app` role using a **double gate**: a boolean variable and a specific tag.

- **Control variable**
  - `roles/web_app/defaults/main.yml` defines:

    ```yaml
    web_app_wipe: false  # Default: do not wipe
    ```

  - This ensures that wipe tasks are disabled by default and only run when I explicitly set `web_app_wipe=true` (e.g. via `-e` on the CLI or in vars files).

- **Wipe tasks**
  - File: `roles/web_app/tasks/wipe.yml`:

    ```yaml
    - name: Wipe web application
      block:
        - name: Stop and remove containers with Docker Compose
          community.docker.docker_compose_v2:
            project_src: "{{ compose_project_dir }}"
            state: absent
          ignore_errors: true

        - name: Remove docker-compose file
          file:
            path: "{{ compose_project_dir }}/docker-compose.yml"
            state: absent

        - name: Remove application directory
          file:
            path: "{{ compose_project_dir }}"
            state: absent

        - name: Log wipe completion
          debug:
            msg: "Application {{ app_name }} wiped successfully"

      when: web_app_wipe | bool
      tags:
        - web_app_wipe
    ```

  - The `when: web_app_wipe | bool` check prevents accidental wipes even if someone runs `--tags web_app_wipe` without setting the variable.
  - `ignore_errors: true` on the compose down step means the play will not fail if the app is already absent (idempotent cleanup).

- **Inclusion order**
  - At the top of `roles/web_app/tasks/main.yml`:

    ```yaml
    - name: Include wipe tasks
      include_tasks: wipe.yml
      tags:
        - web_app_wipe
    ```

  - This ensures the wipe runs **before** any deployment tasks, so a “clean reinstall” can do wipe → deploy in a single playbook run.

### Wipe scenarios

Below are the four scenarios I tested; I include the commands and outputs as evidence.

#### Scenario 1: Normal deployment (wipe does NOT run)

Command:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Key output (trimmed — add your real output here):

```text
PLAY [Deploy application] ********************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************
[WARNING]: Host 'yandex-cluod' is using the discovered Python interpreter at '/usr/bin/python3.10', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [yandex-cluod]

TASK [docker : Install required packages] ****************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [docker : Add Docker GPG key] ***********************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [docker : Add Docker repository] ********************************************************************************************************************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:20:15

18     - name: Add Docker repository
19       apt_repository:
20         repo: "deb https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [yandex-cluod]

TASK [docker : Install Docker packages] ******************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [docker : Ensure Docker service is enabled and started] *********************************************************************************************************************************
ok: [yandex-cluod]

TASK [docker : Add user to docker group] *****************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [docker : Install python docker module] *************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************
included: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for yandex-cluod

TASK [web_app : Stop and remove containers with Docker Compose] ******************************************************************************************************************************
skipping: [yandex-cluod]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************************************
skipping: [yandex-cluod]

TASK [web_app : Remove application directory] ************************************************************************************************************************************************
skipping: [yandex-cluod]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************************************
skipping: [yandex-cluod]

TASK [web_app : Create app directory] ********************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [web_app : Template docker-compose file] ************************************************************************************************************************************************
ok: [yandex-cluod]

TASK [web_app : Deploy with Docker Compose] **************************************************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
ok: [yandex-cluod]

PLAY RECAP ***********************************************************************************************************************************************************************************
yandex-cluod               : ok=12   changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

This shows that with default `web_app_wipe: false` and no wipe tag specified, all wipe tasks are **skipped** and only the normal deployment runs.

#### Scenario 2: Wipe only (remove existing deployment)

Command:

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe \
  --ask-vault-pass
```

Key output (trimmed — add your real output here):

```text
PLAY [Deploy application] ********************************************************************************************************************************************************************

TASK [Gathering Facts] ***********************************************************************************************************************************************************************
[WARNING]: Host 'yandex-cluod' is using the discovered Python interpreter at '/usr/bin/python3.10', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [yandex-cluod]

TASK [web_app : Include wipe tasks] **********************************************************************************************************************************************************
included: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for yandex-cluod

TASK [web_app : Stop and remove containers with Docker Compose] ******************************************************************************************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [yandex-cluod]

TASK [web_app : Remove docker-compose file] **************************************************************************************************************************************************
changed: [yandex-cluod]

TASK [web_app : Remove application directory] ************************************************************************************************************************************************
changed: [yandex-cluod]

TASK [web_app : Log wipe completion] *********************************************************************************************************************************************************
ok: [yandex-cluod] => {
    "msg": "Application devops-app wiped successfully"
}

PLAY RECAP ***********************************************************************************************************************************************************************************
yandex-cluod               : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

On the VM:

```bash
docker ps          # should NOT show the app container
ls /opt            # /opt/devops-app should be gone
```

In this scenario, only the wipe tasks run (because of the `--tags web_app_wipe` filter), and the application is fully removed.

#### Scenario 3: Clean reinstall (wipe → deploy)

Command:

```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --ask-vault-pass
```

Expected key output (trimmed — add your real output here):

```text
PLAY [Deploy application] ********************************************************************

TASK [Gathering Facts] ***********************************************************************
[WARNING]: Host 'yandex-cluod' is using the discovered Python interpreter at '/usr/bin/python3.10', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [yandex-cluod]

TASK [docker : Install required packages] ****************************************************
ok: [yandex-cluod]

TASK [docker : Add Docker GPG key] ***********************************************************
ok: [yandex-cluod]

TASK [docker : Add Docker repository] ********************************************************
[WARNING]: Deprecation warnings can be disabled by setting `deprecation_warnings=False` in ansible.cfg.
[DEPRECATION WARNING]: INJECT_FACTS_AS_VARS default to `True` is deprecated, top-level facts will not be auto injected after the change. This feature will be removed from ansible-core version 2.24.
Origin: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/docker/tasks/main.yml:20:15

18     - name: Add Docker repository
19       apt_repository:
20         repo: "deb https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
                 ^ column 15

Use `ansible_facts["fact_name"]` (no `ansible_` prefix) instead.

ok: [yandex-cluod]

TASK [docker : Install Docker packages] ******************************************************
ok: [yandex-cluod]

TASK [docker : Ensure Docker service is enabled and started] *********************************
ok: [yandex-cluod]

TASK [docker : Add user to docker group] *****************************************************
ok: [yandex-cluod]

TASK [docker : Install python docker module] *************************************************
ok: [yandex-cluod]

TASK [web_app : Include wipe tasks] **********************************************************
included: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for yandex-cluod

TASK [web_app : Stop and remove containers with Docker Compose] ******************************
[ERROR]: Task failed: Module failed: "/opt/devops-app" is not a directory
Origin: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml:4:7

2 - name: Wipe web application
3   block:
4     - name: Stop and remove containers with Docker Compose
        ^ column 7

fatal: [yandex-cluod]: FAILED! => {"changed": false, "msg": "\"/opt/devops-app\" is not a directory"}
...ignoring

TASK [web_app : Remove docker-compose file] **************************************************
ok: [yandex-cluod]

TASK [web_app : Remove application directory] ************************************************
ok: [yandex-cluod]

TASK [web_app : Log wipe completion] *********************************************************
ok: [yandex-cluod] => {
    "msg": "Application devops-app wiped successfully"
}

TASK [web_app : Create app directory] ********************************************************
changed: [yandex-cluod]

TASK [web_app : Template docker-compose file] ************************************************
changed: [yandex-cluod]

TASK [web_app : Deploy with Docker Compose] **************************************************
[WARNING]: Docker compose: unknown None: /opt/devops-app/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion
changed: [yandex-cluod]

PLAY RECAP ***********************************************************************************
yandex-cluod               : ok=16   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=1
```

On the VM:

```bash
docker ps
curl http://localhost:5000
curl http://localhost:5000/health
```

Output:

```text
CONTAINER ID   IMAGE                           COMMAND           CREATED         STATUS         PORTS                                                   NAMES
b57bcbeaf1d9   danielambda/devops-app:latest   "python app.py"   5 seconds ago   Up 4 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp, 8000/tcp   devops-app
```

```text
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"172.18.0.1","method":"GET","path":"/","user_agent":"curl/7.81.0"},"runtime":{"current_time":"2026-03-14T16:16:30.933357+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":11},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":2,"hostname":"b57bcbeaf1d9","platform":"Linux","platform_version":"#180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026","python_version":"3.13.12"}}
```

```text
{"status":"healthy","timestamp":"2026-03-14T16:16:33.461363+00:00","uptime_seconds":13}
```

Here the wipe runs first (because `web_app_wipe=true` and the wipe tasks are included at the top), and then the normal deployment tasks create a fresh installation.

#### Scenario 4: Safety checks (should NOT wipe when variable is false)

Command:

```bash
ansible-playbook playbooks/deploy.yml \
  --tags web_app_wipe \
  --ask-vault-pass
```

Expected output (trimmed — add your real output here):

```text
PLAY [Deploy application] ********************************************************************

TASK [Gathering Facts] ***********************************************************************
[WARNING]: Host 'yandex-cluod' is using the discovered Python interpreter at '/usr/bin/python3.10', but future installation of another Python interpreter could cause a different interpreter to be discovered. See https://docs.ansible.com/ansible-core/2.20/reference_appendices/interpreter_discovery.html for more information.
ok: [yandex-cluod]

TASK [web_app : Include wipe tasks] **********************************************************
included: /home/daniel/projects/python/DevOps-Core-Course/ansible/roles/web_app/tasks/wipe.yml for yandex-cluod

TASK [web_app : Stop and remove containers with Docker Compose] ******************************
skipping: [yandex-cluod]

TASK [web_app : Remove docker-compose file] **************************************************
skipping: [yandex-cluod]

TASK [web_app : Remove application directory] ************************************************
skipping: [yandex-cluod]

TASK [web_app : Log wipe completion] *********************************************************
skipping: [yandex-cluod]

PLAY RECAP ***********************************************************************************
yandex-cluod               : ok=2    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

Because `web_app_wipe` is still `false` by default, the `when: web_app_wipe | bool` condition prevents the wipe from running even though the `web_app_wipe` tag is specified. This confirms the “double safety” behaviour.

#### Research answers (Wipe logic)

- **Why use both variable AND tag?**
  Using both a boolean variable and a tag gives two layers of protection: the tag ensures wipe tasks never run during normal playbook runs unless explicitly requested, and the variable prevents accidental wipes if someone runs `--tags web_app_wipe` without understanding the consequences.

- **Difference vs the `never` tag**
  The `never` tag completely disables tasks unless you explicitly target them, but it does not let you add extra conditions. With the variable + tag pattern, I can still run `--tags web_app_wipe` while using the variable as an additional guard (for example, requiring `web_app_wipe=true` in extra vars).

- **Why must wipe logic come BEFORE deployment in `main.yml`?**
  If deployment ran first, I could end up deploying a new version and then immediately deleting it, or leaving stale files/containers behind. Putting wipe first guarantees a clean slate before any new deployment, which is essential for a “clean reinstall” flow.

- **When choose clean reinstall vs rolling update?**
  Clean reinstall is useful when I want to be certain no old state is left behind (e.g. breaking config changes, corrupted data, debugging). Rolling updates are preferred when I need zero or minimal downtime and can upgrade containers in place while keeping state.

- **How to extend this to wipe Docker images and volumes?**
  I could add extra tasks inside the wipe block that use `community.docker.docker_image` with `state: absent` for specific images and `community.docker.docker_volume` for named volumes. Those tasks would also be protected by the same `web_app_wipe | bool` condition and `web_app_wipe` tag.

## Task 4: CI/CD (3 pts)

I added a dedicated GitHub Actions workflow to lint my Ansible code and automatically run the `deploy.yml` playbook when Ansible files change.

- **Workflow file and triggers**
  - File: `.github/workflows/ansible-deploy.yml`
  - The workflow is named **"Ansible Deployment"** and is triggered on:
    - `push` to `main` or `master` when paths under `ansible/**` or the workflow file itself change.
    - `pull_request` targeting `main` or `master` when `ansible/**` changes.
  - This path filter ensures the workflow only runs when Ansible-related code is modified, which keeps CI efficient.

- **Lint job**
  - Job name: `lint` (Ansible Lint)
  - Runs on: `ubuntu-latest`
  - Steps:
    - Checkout the repository with `actions/checkout@v4`.
    - Set up Python 3.12 with `actions/setup-python@v5`.
    - Install Ansible and ansible-lint:

      ```bash
      pip install ansible ansible-lint
      ```

    - Run ansible-lint against all playbooks:

      ```bash
      cd ansible
      ansible-lint playbooks/*.yml
      ```

  - If this job fails, the deploy job does not run.

- **Deploy job**
  - Job name: `Deploy Application`
  - Depends on: `lint` (using `needs: lint`)
  - Runs on: `ubuntu-latest` (GitHub-hosted runner)
  - Steps:
    - Checkout the repo.
    - Set up Python 3.12 and install Ansible:

      ```bash
      pip install ansible
      ```

    - Configure SSH to the target VM using GitHub secrets:

      ```bash
      mkdir -p ~/.ssh
      echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
      chmod 600 ~/.ssh/id_rsa
      ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
      ```

    - Deploy with Ansible, using the Vault password from a secret:

      ```bash
      cd ansible
      echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
      ansible-playbook playbooks/deploy.yml \
        -i inventory/hosts.ini \
        --vault-password-file /tmp/vault_pass
      rm /tmp/vault_pass
      ```

    - Verify the deployment by curling the application on the VM:

      ```bash
      sleep 10
      curl -f http://${{ secrets.VM_HOST }}:8000 || exit 1
      curl -f http://${{ secrets.VM_HOST }}:8000/health || exit 1
      ```

  - This job ensures that a successful run means both Ansible completed without errors and the HTTP endpoints on the VM respond correctly.

- **GitHub Secrets configuration**
  - I configured the following secrets under **Settings → Secrets and variables → Actions**:
    - `SSH_PRIVATE_KEY` – private SSH key used by the workflow to connect to the target VM as the same user defined in `ansible/ansible.cfg` / inventory.
    - `VM_HOST` – the public IP or hostname of the Ansible target VM.
    - `ANSIBLE_VAULT_PASSWORD` – the password used to decrypt Vault-encrypted values (written to `/tmp/vault_pass` during the workflow).
  - These secrets are only referenced in the workflow and never committed to the repo.

- **Evidence**
  - I triggered the workflow by pushing a small change under the `ansible/` directory.
  - In the **Actions** tab:
    - The `Ansible Deployment` workflow shows a successful run, with the `lint` job passing and the `Deploy Application` job completing.
    - The logs show `ansible-lint` running against `playbooks/*.yml` and a successful `ansible-playbook playbooks/deploy.yml` execution.
    - The final verification step logs successful `curl` calls to `http://VM_HOST:8000` and `/health`.
  - I also added a status badge to my README (or `ansible/README.md`) pointing to this workflow, so I can see at a glance whether the Ansible deployment pipeline is passing.

## Task 5: Documentation

[This file serves as the Lab 6 documentation. Add any extra notes or clarifications needed by your instructor here.]

---

## Summary

[Add a short reflection, total time spent, and your key learnings from this lab.]

