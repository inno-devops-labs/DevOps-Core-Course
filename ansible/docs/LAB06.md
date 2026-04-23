# Lab 6: Advanced Ansible & CI/CD — Submission

**Name:** Makar  
**Date:** 2026-03-04  
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

### 1.1 Block Usage in Common Role

**File:** `roles/common/tasks/main.yml`

The common role was refactored into a single block that groups all package-related tasks together. The block applies `become: true` once at the block level rather than per-task, and uses the tags `packages` and `common`.

```yaml
---
# Package installation block with error handling
- name: Install system packages
  become: true
  tags:
    - packages
    - common
  block:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Install common packages
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present

    - name: Set timezone
      community.general.timezone:
        name: "{{ common_timezone }}"

  rescue:
    - name: Fix apt cache on failure
      ansible.builtin.apt:
        update_cache: true
        force: true

    - name: Retry package installation after fix
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present
        update_cache: true

  always:
    - name: Log package installation completion
      ansible.builtin.copy:
        content: "Common role packages block completed at {{ ansible_date_time.iso8601 }}\n"
        dest: /tmp/common_packages_done.log
        mode: "0644"
```

**Error handling:** If `apt update` or package installation fails, the rescue block runs `apt update --force` and retries. The always block logs a timestamp to `/tmp/common_packages_done.log` regardless of success or failure.

### 1.2 Block Usage in Docker Role

**File:** `roles/docker/tasks/main.yml`

The docker role was split into two logical blocks:

1. **Install Docker Engine** (`docker_install` tag) — groups prerequisites, GPG key, repository, and package installation with rescue/always error handling.
2. **Configure Docker** (`docker_config` tag) — groups user and Python library setup.

```yaml
---
# Docker installation block with error handling
- name: Install Docker Engine
  become: true
  tags:
    - docker_install
    - docker
  block:
    - name: Install prerequisites for Docker repository
      ansible.builtin.apt:
        name: [ca-certificates, curl, gnupg]
        state: present
    - name: Create keyrings directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"
    - name: Add Docker GPG key
      ansible.builtin.apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        keyring: /etc/apt/keyrings/docker.gpg
        state: present
    - name: Add Docker repository
      ansible.builtin.apt_repository:
        repo: >-
          deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg]
          https://download.docker.com/linux/ubuntu
          {{ ansible_facts['distribution_release'] }} stable
        state: present
        filename: docker
    - name: Install Docker packages
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
        update_cache: true
      notify: Restart docker
  rescue:
    - name: Wait before retrying Docker installation
      ansible.builtin.pause:
        seconds: 10
    - name: Retry apt update after GPG key failure
      ansible.builtin.apt:
        update_cache: true
    - name: Retry Docker package installation
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
      notify: Restart docker
  always:
    - name: Ensure Docker service is enabled and started
      ansible.builtin.service:
        name: docker
        state: started
        enabled: true
      failed_when: false

# Docker configuration block
- name: Configure Docker
  become: true
  tags:
    - docker_config
    - docker
  block:
    - name: Add user to docker group
      ansible.builtin.user:
        name: "{{ docker_user }}"
        groups: docker
        append: true
    - name: Install python3-docker for Ansible docker modules
      ansible.builtin.apt:
        name: python3-docker
        state: present
```

**Error handling:** The Docker GPG key addition can fail due to network timeouts. The rescue block waits 10 seconds, retries `apt update`, then retries package installation. The always block ensures the Docker service is enabled regardless of outcome.

### 1.3 Tag Strategy

| Tag | Scope | Description |
|-----|-------|-------------|
| `common` | common role | All common role tasks |
| `packages` | common role | Package installation tasks |
| `docker` | docker role | All Docker tasks |
| `docker_install` | docker role | Docker installation only |
| `docker_config` | docker role | Docker configuration only |
| `app_deploy` | web_app role | Application deployment |
| `compose` | web_app role | Docker Compose operations |
| `web_app_wipe` | web_app role | Wipe/cleanup tasks |

### 1.4 Evidence — ansible-lint Passes (Production Profile)

```
$ cd ansible && source ../app_python/venv/bin/activate.fish && ansible-lint playbooks/*.yml

Passed: 0 failure(s), 0 warning(s) on 13 files examined and 11 of them are considered (2 exempted).
Last profile that matched before the error was 'production'.
```

All roles pass the strictest production-level lint profile with zero warnings.

### 1.5 Evidence — Tag Listing

```
$ ansible-playbook playbooks/provision.yml --list-tags
  play #1 (webservers): Provision infrastructure  TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages]

$ ansible-playbook playbooks/deploy.yml --list-tags
  play #1 (webservers): Deploy application        TAGS: []
      TASK TAGS: [app_deploy, compose, docker, docker_config, docker_install, web_app_wipe]
```

Note: `deploy.yml` includes docker tags because `web_app/meta/main.yml` declares `docker` as a dependency.

### 1.6 Evidence — Selective Tag Execution (only docker tasks)

```
$ ansible-playbook playbooks/provision.yml --tags "docker" \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY [Provision infrastructure] ************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops_vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [devops_vm]

TASK [docker : Create keyrings directory] **************************************
ok: [devops_vm]

TASK [docker : Add Docker GPG key] *********************************************
ok: [devops_vm]

TASK [docker : Add Docker repository] ******************************************
ok: [devops_vm]

TASK [docker : Install Docker packages] ****************************************
ok: [devops_vm]

TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [devops_vm]

TASK [docker : Add user to docker group] ***************************************
ok: [devops_vm]

TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [devops_vm]

PLAY RECAP *********************************************************************
devops_vm  : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

All common role tasks (Update apt cache, Install common packages, Set timezone, Log) were **skipped** because they don't carry the `docker` tag — only docker role tasks executed.

### 1.7 Evidence — Rescue Block Triggered

During initial deployment, the rescue block was triggered due to a container name conflict (leftover from Lab 5):

```
TASK [web_app : Deploy with docker compose] ************************************
fatal: [devops_vm]: FAILED! => ...
  "stderr": "Error response from daemon: Conflict. The container name \"/devops-app\"
   is already in use by container ... You have to remove (or rename) that container..."

TASK [web_app : Log deployment failure] ****************************************
ok: [devops_vm] => {
    "msg": "Deployment of devops-app failed. Check logs with:
     docker compose -f /opt/devops-app/docker-compose.yml logs"
}

TASK [web_app : Fail with error message] ***************************************
fatal: [devops_vm]: FAILED! ...

PLAY RECAP *********************************************************************
devops_vm  : ok=16   changed=3    unreachable=0    failed=1    skipped=1    rescued=1    ignored=0
```

The `rescued=1` confirms the rescue block fired. After removing the conflicting container (`docker rm -f devops-app`), re-deployment succeeded.

### 1.8 Research Answers — Blocks & Tags

**Q: What happens if rescue block also fails?**  
If the rescue block fails, the **always** block still runs (if present), but the overall task/play is marked as failed. Ansible does NOT have a "rescue for the rescue" — the play stops for that host after the always block completes.

**Q: Can you have nested blocks?**  
Yes, blocks can be nested. Inner blocks can have their own rescue/always sections. However, deeply nested blocks reduce readability — typically one level is sufficient.

**Q: How do tags inherit to tasks within blocks?**  
Tags applied at the block level are inherited by all tasks within the block (including rescue and always sections). Tags on individual tasks inside a block are additive — a task gets both the block's tags and its own tags.

---

## Task 2: Docker Compose (3 pts)

### 2.1 Role Rename

Renamed `app_deploy` → `web_app` for clarity:
```bash
cd ansible/roles && mv app_deploy web_app
```

All playbook references updated: `deploy.yml`, `site.yml`.

### 2.2 Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

```yaml
# {{ ansible_managed }}
# Docker Compose configuration for {{ web_app_name }}

services:
  {{ web_app_name }}:
    image: {{ web_app_image }}:{{ web_app_tag }}
    container_name: {{ web_app_name }}
    ports:
      - "{{ web_app_port }}:{{ web_app_internal_port }}"
{% if web_app_env | length > 0 %}
    environment:
{% for key, value in web_app_env.items() %}
      {{ key }}: "{{ value }}"
{% endfor %}
{% endif %}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ web_app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Features:**
- Dynamic service name, image, ports via Jinja2 variables
- Conditional environment block (only rendered if `web_app_env` has entries)
- Built-in Docker healthcheck for self-healing
- `unless-stopped` restart policy (survives host reboots, respects manual stops)
- `ansible_managed` comment to indicate the file is generated

### 2.3 Role Dependencies

**File:** `roles/web_app/meta/main.yml`

```yaml
---
dependencies:
  - role: docker
```

This ensures Docker is automatically installed before `web_app` deploys. Running `ansible-playbook playbooks/deploy.yml` triggers the docker role first without needing it in the playbook.

### 2.4 Deployment Tasks

**File:** `roles/web_app/tasks/main.yml`

```yaml
---
# Wipe logic runs first (when explicitly requested)
- name: Include wipe tasks
  ansible.builtin.include_tasks: wipe.yml
  tags:
    - web_app_wipe

# Deploy application with Docker Compose
- name: Deploy application with Docker Compose
  become: true
  tags:
    - app_deploy
    - compose
  block:
    - name: Create application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}"
        state: directory
        mode: "0755"

    - name: Template docker-compose file
      ansible.builtin.template:
        src: docker-compose.yml.j2
        dest: "{{ web_app_compose_dir }}/docker-compose.yml"
        mode: "0644"
      register: web_app_compose_file

    - name: Log in to Docker Hub
      community.docker.docker_login:
        username: "{{ dockerhub_username }}"
        password: "{{ dockerhub_password }}"
      no_log: true

    - name: Pull latest Docker image
      community.docker.docker_image:
        name: "{{ web_app_image }}"
        tag: "{{ web_app_tag }}"
        source: pull
      register: web_app_image_pull

    - name: Deploy with docker compose
      ansible.builtin.command:
        cmd: docker compose up -d --remove-orphans
        chdir: "{{ web_app_compose_dir }}"
      register: web_app_compose_up
      changed_when: >-
        'Started' in web_app_compose_up.stderr or
        'Created' in web_app_compose_up.stderr or
        web_app_compose_file.changed or
        web_app_image_pull.changed

    - name: Wait for application to be ready
      ansible.builtin.wait_for:
        port: "{{ web_app_port }}"
        host: "127.0.0.1"
        delay: 5
        timeout: 30

    - name: Verify health endpoint
      ansible.builtin.uri:
        url: "http://127.0.0.1:{{ web_app_port }}/health"
        method: GET
        return_content: true
        status_code: 200
      register: web_app_health_check
      retries: 3
      delay: 5

    - name: Display health check result
      ansible.builtin.debug:
        var: web_app_health_check.json

  rescue:
    - name: Log deployment failure
      ansible.builtin.debug:
        msg: >-
          Deployment of {{ web_app_name }} failed. Check logs with:
          docker compose -f {{ web_app_compose_dir }}/docker-compose.yml logs

    - name: Fail with error message
      ansible.builtin.fail:
        msg: "Docker Compose deployment failed for {{ web_app_name }}"
```

**Before (Lab 5):** Used `community.docker.docker_container` module to run individual containers with `docker run` semantics.

**After (Lab 6):** Uses `docker compose up -d` with a templated `docker-compose.yml`:

1. Create `/opt/devops-app/` directory
2. Template `docker-compose.yml.j2` → `/opt/devops-app/docker-compose.yml`
3. Login to Docker Hub (credentials from Vault)
4. Pull the latest image
5. Run `docker compose up -d --remove-orphans`
6. Wait for port + verify `/health` endpoint

### 2.5 Variables Configuration

**File:** `roles/web_app/defaults/main.yml`

```yaml
---
web_app_name: devops-app
web_app_port: 5000
web_app_internal_port: 5000
web_app_env: {}
web_app_image: graymansion/devops-info-service
web_app_tag: latest
web_app_compose_dir: "/opt/{{ web_app_name }}"
web_app_wipe: false
```

Sensitive values (`dockerhub_username`, `dockerhub_password`) remain in Vault-encrypted `group_vars/all.yml`.

### 2.6 Evidence — Successful Docker Compose Deployment

```
$ ansible-playbook playbooks/deploy.yml \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops_vm]

TASK [docker : Install prerequisites for Docker repository] ********************
ok: [devops_vm]
...
TASK [docker : Ensure Docker service is enabled and started] *******************
ok: [devops_vm]
TASK [docker : Add user to docker group] ***************************************
ok: [devops_vm]
TASK [docker : Install python3-docker for Ansible docker modules] **************
ok: [devops_vm]

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for devops_vm

TASK [web_app : Wipe web application] ******************************************
skipping: [devops_vm]

TASK [web_app : Create application directory] **********************************
ok: [devops_vm]

TASK [web_app : Template docker-compose file] **********************************
ok: [devops_vm]

TASK [web_app : Log in to Docker Hub] ******************************************
ok: [devops_vm]

TASK [web_app : Pull latest Docker image] **************************************
ok: [devops_vm]

TASK [web_app : Deploy with docker compose] ************************************
ok: [devops_vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [devops_vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [devops_vm]

TASK [web_app : Display health check result] ***********************************
ok: [devops_vm] => {
    "web_app_health_check.json": {
        "status": "healthy",
        "timestamp": "2026-03-04T13:21:46.507Z",
        "uptime_seconds": 60
    }
}

PLAY RECAP *********************************************************************
devops_vm  : ok=18   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

### 2.7 Evidence — Idempotency (Second Run, changed=0)

```
$ ansible-playbook playbooks/deploy.yml \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY RECAP *********************************************************************
devops_vm  : ok=18   changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

`changed=0` confirms full idempotency. Wipe task is `skipped=1` (variable gate is false by default).

### 2.8 Evidence — Rendered docker-compose.yml on VM

```
$ ssh vagrant@192.168.121.159 cat /opt/devops-app/docker-compose.yml
# Ansible managed
# Docker Compose configuration for devops-app

services:
  devops-app:
    image: graymansion/devops-info-service:latest
    container_name: devops-app
    ports:
      - "5000:5000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 2.9 Evidence — Container Running

```
$ ssh vagrant@192.168.121.159 docker ps
CONTAINER ID   IMAGE                                      STATUS                    PORTS                    NAMES
2ac8c632334c   graymansion/devops-info-service:latest      Up 3 minutes (healthy)    0.0.0.0:5000->5000/tcp   devops-app
```

### 2.10 Evidence — Curl Verification

```
$ curl -s http://192.168.121.159:5000/ | python3 -m json.tool
{
    "service": {
        "name": "DevOps Information Service",
        "version": "1.0.0",
        "description": "Lightweight Python web app crafted for DevOps Core Course labs"
    },
    "system": {
        "hostname": "2ac8c632334c",
        "platform": "Linux-5.15.0-130-generic-x86_64-with-glibc2.36",
        "python_version": "3.11.12",
        "cpu_count": 2,
        "memory_total_mb": 1972.83
    },
    "runtime": {
        "start_time": "2026-03-04T13:20:46.487181+00:00",
        "uptime_seconds": 92.099...
    },
    "request": {
        "remote_addr": "192.168.121.1",
        "method": "GET",
        "path": "/",
        "timestamp": "2026-03-04T13:22:18.586Z"
    }
}

$ curl -s http://192.168.121.159:5000/health | python3 -m json.tool
{
    "status": "healthy",
    "timestamp": "2026-03-04T13:22:18.585Z",
    "uptime_seconds": 92
}
```

### 2.11 Research Answers — Docker Compose

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**  
`always` restarts the container unconditionally, even after a manual `docker stop`. `unless-stopped` also restarts on failure/reboot, but respects a manual stop — if you explicitly stop a container, it stays stopped until you start it again. `unless-stopped` is preferred for production since operators can intentionally stop services.

**Q: How do Docker Compose networks differ from Docker bridge networks?**  
Docker Compose creates a project-specific bridge network (named `<project>_default`) where services can reach each other by service name. Manual `docker run` uses the default `bridge` network where container-to-container communication requires explicit `--link` or network creation. Compose networks provide automatic DNS-based service discovery.

**Q: Can you reference Ansible Vault variables in the template?**  
Yes. Vault-encrypted variables are decrypted at runtime and available to Jinja2 templates exactly like plaintext variables. You can use `{{ vault_var }}` in templates; the rendered file contains the decrypted value. Be cautious — the rendered file on disk is plaintext, so set proper file permissions.

---

## Task 3: Wipe Logic (1 pt)

### 3.1 Implementation Details

**File:** `roles/web_app/tasks/wipe.yml`

```yaml
---
# Wipe tasks for web application — requires BOTH:
#   1. Variable: web_app_wipe=true  (when condition)
#   2. Tag: --tags web_app_wipe     (tag gating)
# This double-safety prevents accidental wipe during normal deployments.

- name: Wipe web application
  when: web_app_wipe | bool
  become: true
  tags:
    - web_app_wipe
  block:
    - name: Stop and remove containers with docker compose
      ansible.builtin.command:
        cmd: docker compose down --remove-orphans
        chdir: "{{ web_app_compose_dir }}"
      changed_when: true
      failed_when: false

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_dir }}"
        state: absent

    - name: Remove Docker image (optional cleanup)
      community.docker.docker_image:
        name: "{{ web_app_image }}"
        tag: "{{ web_app_tag }}"
        state: absent
      failed_when: false

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ web_app_name }} wiped successfully from {{ web_app_compose_dir }}"
```

### 3.2 Double-Safety Mechanism

Wipe requires **both** conditions:
1. **Variable gate:** `when: web_app_wipe | bool` (default: `false`)
2. **Tag gate:** `tags: [web_app_wipe]` (only runs when this tag is explicitly specified or all tags are run)

During normal `ansible-playbook deploy.yml` (no `--tags` flag), **all** tags run, but the `when` condition blocks wipe (variable is `false`). This means wipe never runs accidentally.

### 3.3 Wipe Ordering in main.yml

Wipe is included **before** deployment tasks to support the clean reinstall pattern (wipe old → deploy new):

```yaml
# Wipe logic runs first
- name: Include wipe tasks
  ansible.builtin.include_tasks: wipe.yml
  tags: [web_app_wipe]

# Then deployment
- name: Deploy application with Docker Compose
  block: ...
  tags: [app_deploy, compose]
```

### 3.4 Evidence — Scenario 4a: Tag Without Variable (Safety Check)

```
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops_vm]

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for devops_vm

TASK [web_app : Wipe web application] ******************************************
skipping: [devops_vm]

PLAY RECAP *********************************************************************
devops_vm  : ok=2    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

The wipe block is **skipped** because `web_app_wipe` defaults to `false`. Even with the tag selected, the variable gate prevents any destructive action.

### 3.5 Evidence — Scenario 2: Wipe Only

```
$ ansible-playbook playbooks/deploy.yml \
    -e "web_app_wipe=true" --tags web_app_wipe \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops_vm]

TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for devops_vm

TASK [web_app : Stop and remove containers with docker compose] ****************
changed: [devops_vm]

TASK [web_app : Remove docker-compose file] ************************************
changed: [devops_vm]

TASK [web_app : Remove application directory] **********************************
changed: [devops_vm]

TASK [web_app : Remove Docker image (optional cleanup)] ************************
ok: [devops_vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [devops_vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

PLAY RECAP *********************************************************************
devops_vm  : ok=7    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Wipe removed the running containers, compose file, and application directory. Deployment tasks were **not run** because they carry `app_deploy`/`compose` tags (filtered out by `--tags web_app_wipe`).

**Verification after wipe:**
```
$ ssh vagrant@192.168.121.159 docker ps
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES

$ ssh vagrant@192.168.121.159 ls /opt/devops-app
ls: cannot access '/opt/devops-app': No such file or directory
```

No containers running. Application directory removed.

### 3.6 Evidence — Scenario 3: Clean Reinstallation (Wipe + Deploy)

```
$ ansible-playbook playbooks/deploy.yml \
    -e "web_app_wipe=true" \
    -i inventory/hosts.ini --vault-password-file /tmp/.vault_pass

PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [devops_vm]
...
TASK [web_app : Include wipe tasks] ********************************************
included: .../roles/web_app/tasks/wipe.yml for devops_vm

TASK [web_app : Stop and remove containers with docker compose] ****************
changed: [devops_vm]

TASK [web_app : Remove docker-compose file] ************************************
changed: [devops_vm]

TASK [web_app : Remove application directory] **********************************
changed: [devops_vm]

TASK [web_app : Remove Docker image (optional cleanup)] ************************
changed: [devops_vm]

TASK [web_app : Log wipe completion] *******************************************
ok: [devops_vm] => {
    "msg": "Application devops-app wiped successfully from /opt/devops-app"
}

TASK [web_app : Create application directory] **********************************
changed: [devops_vm]

TASK [web_app : Template docker-compose file] **********************************
changed: [devops_vm]

TASK [web_app : Log in to Docker Hub] ******************************************
ok: [devops_vm]

TASK [web_app : Pull latest Docker image] **************************************
changed: [devops_vm]

TASK [web_app : Deploy with docker compose] ************************************
changed: [devops_vm]

TASK [web_app : Wait for application to be ready] ******************************
ok: [devops_vm]

TASK [web_app : Verify health endpoint] ****************************************
ok: [devops_vm]

TASK [web_app : Display health check result] ***********************************
ok: [devops_vm] => {
    "web_app_health_check.json": {
        "status": "healthy",
        "timestamp": "...",
        "uptime_seconds": 6
    }
}

PLAY RECAP *********************************************************************
devops_vm  : ok=23   changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

`changed=8` = 4 wipe changes + 4 deploy changes. The application was completely removed and re-deployed from scratch in a single playbook run.

### 3.7 Evidence — Scenario 1: Normal Deployment (Wipe Skipped)

This is the default behavior shown in Section 2.6. When `web_app_wipe` defaults to `false`:

```
TASK [web_app : Wipe web application] ******************************************
skipping: [devops_vm]
```

The wipe block is skipped, deployment proceeds normally. `skipped=1` in the PLAY RECAP.

### 3.8 Research Answers — Wipe Logic

**1. Why use both variable AND tag?**  
Double safety. The variable prevents wipe when someone accidentally adds the wrong `--tags`. The tag prevents wipe during normal deployments (where all tags run). Neither alone is sufficient.

**2. What's the difference between `never` tag and this approach?**  
The `never` tag is a special Ansible tag that causes tasks to be skipped unless explicitly included with `--tags never`. Our approach uses a custom tag + variable gate. The `never` tag approach lacks the variable safety — anyone running `--tags never` would trigger wipe. Our approach requires both `--tags web_app_wipe` AND `-e "web_app_wipe=true"`.

**3. Why must wipe logic come BEFORE deployment in main.yml?**  
For the clean reinstall use case: when running `ansible-playbook deploy.yml -e "web_app_wipe=true"` (no tag filter), both wipe and deploy execute. Wipe must run first to remove old state before fresh deployment replaces it.

**4. When would you want clean reinstallation vs. rolling update?**  
Clean reinstall is needed when: migrating to a different compose config structure, debugging persistent state issues, changing container names/networks. Rolling updates are preferred for routine version bumps with zero downtime.

**5. How would you extend this to wipe Docker images and volumes too?**  
Add `docker compose down --rmi all --volumes` to remove images and named volumes. Add `docker system prune -f` for dangling resources. Our implementation already removes the Docker image as an optional step.

---

## Task 4: CI/CD (3 pts)

### 4.1 Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

```
Push to ansible/** → Lint Job → Deploy Job → Verify Deployment
```

Two-job pipeline:
1. **lint** — runs `ansible-lint` on all playbooks
2. **deploy** — installs Ansible, configures SSH, deploys via playbook, verifies app

### 4.2 Full Workflow Configuration

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'

concurrency:
  group: ansible-deploy-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install ansible ansible-lint
      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Ansible
        run: pip install ansible
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
      - name: Deploy with Ansible
        env:
          ANSIBLE_HOST_KEY_CHECKING: "False"
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            --vault-password-file /tmp/vault_pass
          rm -f /tmp/vault_pass
      - name: Verify Deployment
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:5000 || exit 1
          curl -f http://${{ secrets.VM_HOST }}:5000/health || exit 1
```

### 4.3 Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_VAULT_PASSWORD` | Decrypts Vault-encrypted variables |
| `SSH_PRIVATE_KEY` | SSH key for target VM access |
| `VM_HOST` | Target VM IP address (192.168.121.159) |

### 4.4 Path Filters

Ansible workflow only triggers on changes to:
- `ansible/**` (all Ansible code)
- `.github/workflows/ansible-deploy.yml` (workflow itself)

Excluded: `ansible/docs/**` (documentation changes don't need deployment).

### 4.5 Concurrency Control

```yaml
concurrency:
  group: ansible-deploy-${{ github.ref }}
  cancel-in-progress: true
```

Prevents multiple deployment runs from overlapping on the same branch. If a new push arrives while a deployment is running, the old one is cancelled.

### 4.6 Verification Step

After deployment, the workflow waits 10 seconds and verifies:
```bash
curl -f http://$VM_HOST:5000       # Main endpoint
curl -f http://$VM_HOST:5000/health  # Health endpoint
```

### 4.7 Status Badge in README.md

```markdown
[![Ansible Deployment](https://github.com/GrayMansion/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/GrayMansion/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)
```

Added to the top of `README.md` alongside the existing Python CI badge.

### 4.8 Research Answers — CI/CD

**1. What are the security implications of storing SSH keys in GitHub Secrets?**  
GitHub Secrets are encrypted at rest and masked in logs. However, any workflow code in the repository can access them, so a malicious PR could exfiltrate secrets if workflow runs on PRs with write access. Mitigations: use environment protection rules, require approval for workflow runs from forks, use short-lived credentials or deploy keys with minimal permissions.

**2. How would you implement a staging → production deployment pipeline?**  
Use GitHub environments (`staging`, `production`) with protection rules. Deploy to staging automatically on push, require manual approval for production. Use separate inventory files or host groups for each environment. Add integration tests between stages.

**3. What would you add to make rollbacks possible?**  
Pin Docker image tags (not `latest`) using CalVer or SemVer. Store the previous tag in a variable/file. On rollback, redeploy with the previous tag. Alternatively, use the wipe + deploy pattern with the old image tag: `-e "web_app_tag=2026.02.15"`.

**4. How does self-hosted runner improve security compared to GitHub-hosted?**  
Self-hosted runners are within your network, reducing the attack surface — no SSH keys need to be stored in GitHub Secrets since the runner has direct local access. However, self-hosted runners require maintenance (updates, security patches) and can be a risk if compromised, since they have network access to production infrastructure.

---

## Task 5: Documentation

This document serves as the complete Lab 6 documentation.

### Updated File Structure

```
ansible/
├── ansible.cfg
├── Vagrantfile
├── docs/
│   ├── LAB05.md
│   └── LAB06.md                    # This file
├── inventory/
│   ├── hosts.ini
│   └── group_vars/
│       └── all.yml                 # Vault-encrypted
├── playbooks/
│   ├── deploy.yml                  # Updated: web_app role
│   ├── provision.yml
│   └── site.yml                    # Updated: web_app role
└── roles/
    ├── common/
    │   ├── defaults/main.yml
    │   └── tasks/main.yml          # Refactored: blocks, tags, rescue/always
    ├── docker/
    │   ├── defaults/main.yml
    │   ├── handlers/main.yml
    │   └── tasks/main.yml          # Refactored: blocks, tags, rescue/always
    └── web_app/                    # Renamed from app_deploy
        ├── defaults/main.yml       # Updated: compose vars, wipe var
        ├── handlers/main.yml       # Updated: compose restart
        ├── meta/main.yml           # NEW: role dependencies
        ├── tasks/
        │   ├── main.yml            # Rewritten: compose deployment
        │   └── wipe.yml            # NEW: wipe logic
        └── templates/
            └── docker-compose.yml.j2  # NEW: Jinja2 template

.github/workflows/
├── python-ci.yml           # Existing: Python app CI
└── ansible-deploy.yml      # NEW: Ansible deployment CD
```


## Challenges & Solutions

1. **ansible-lint production profile:** Required multiple iterations to fix `yaml[truthy]` (yes→true), `var-naming[no-role-prefix]` (all vars prefixed `web_app_`), `name[casing]` (handler names capitalized), `key-order` (`become`/`tags` before `block`), `ignore-errors` (replaced with `failed_when: false`), `command-instead-of-module` (replaced shell command with `ansible.builtin.apt`), and `yaml[line-length]` (multi-line `changed_when` with `>-`).

2. **Container name conflict:** Lab 5 left a container named `devops-app` (created with `docker_container` module). Docker Compose couldn't claim that name. The rescue block correctly caught the error (`rescued=1`), and after removing the old container, redeployment succeeded.

---

## Summary

- **Time spent:** ~3 hours
- **Key learnings:**
  - Ansible blocks provide clean error handling (rescue) and guaranteed cleanup (always)
  - Tags enable selective execution — critical for large playbooks in production
  - Docker Compose via templates is more maintainable than `docker run` commands
  - Role dependencies automate execution order
  - Double-gated wipe logic prevents accidental data loss
  - CI/CD with path filters avoids unnecessary workflow runs
  - ansible-lint production profile enforces consistent code quality
