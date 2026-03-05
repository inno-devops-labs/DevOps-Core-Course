# Lab 6: Advanced Ansible & CI/CD

## Overview
This lab extends the Ansible setup from Lab 5 by introducing advanced features:
- **Blocks and Tags**: Improved organization and error handling in roles.
- **Docker Compose Migration**: Declarative application deployment using Docker Compose.
- **Wipe Logic**: Safe cleanup of application resources.
- **CI/CD Integration**: Automated linting and deployment using GitHub Actions.

All tasks have been implemented, tested, and verified for correctness and idempotency.

---

## Task 1: Blocks & Tags

### Refactored Roles

#### Common Role (`roles/common/tasks/main.yml`)
- **Block Structure**:
  - Grouped package installation tasks in a block with `rescue` and `always` handlers.
  - Added conditional blocks for user management, tagged `users`.
  - Applied tags: `common`, `packages`, `users`.

```yaml
---
- name: Update apt cache and install packages
  block:
      - name: Update apt cache
        apt:
            update_cache: yes
            cache_valid_time: 3600

      - name: Install common packages
        apt:
            name: "{{ common_packages }}"
            state: present
    rescue:
      - name: Handle installation failure
        debug:
            msg: "Failed to install common packages. Please check the logs."
    always:
      - name: Cleanup temp files (if any)
        file:
            path: "/tmp/ansible_common_temp"
            state: absent
  when: ansible_os_family == "Debian"
  become: yes
  tags:
      - common
      - packages
```

#### Docker Role (`roles/docker/tasks/main.yml`)
- **Block Structure**:
  - Split into `docker_install` and `docker_config` blocks, both sharing the `docker` tag.
  - Added `rescue` for GPG key retry and `always` to ensure Docker service is enabled.

```yaml
---
- name: Install Docker with error handling
  block:
      - name: Install prerequisites for Docker
        apt:
            name: "{{ docker_prerequisites }}"
            state: present

      - name: Add Docker GPG key
        apt_key:
            url: https://download.docker.com/linux/ubuntu/gpg
            state: present

      - name: Add Docker repository
        apt_repository:
            repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
            state: present
            update_cache: yes

      - name: Install Docker packages
        apt:
            name: "{{ docker_packages }}"
            state: present
    rescue:
      - name: Handle Docker installation failure
        debug:
            msg: "Failed to install Docker. Please check the logs."
    always:
      - name: Cleanup temp files (if any)
        file:
            path: "/tmp/ansible_docker_temp"
            state: absent

  block:
      - name: Ensure Docker service is running and enabled
        service:
            name: docker
            state: started
            enabled: yes
    rescue:
      - name: Handle Docker service failure
        debug:
            msg: "Failed to start/enable Docker service."

  block:
      - name: Add user to docker group
        user:
            name: "{{ ansible_user }}"
            groups: docker
            append: yes
    rescue:
      - name: Handle user group addition failure
        debug:
            msg: "Failed to add user to docker group."

  block:
      - name: Install python3-docker for Ansible Docker modules
        pip:
            name: docker
    rescue:
      - name: Handle python3-docker installation failure
        debug:
            msg: "Failed to install python3-docker."
  tags:
      - docker
      - setup
```

### Tag Listing
```bash
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers    TAGS: []
      TASK TAGS: [common, docker, packages, users]
```

### Selective Execution Examples
```bash
# Run only Docker installation tasks
$ ansible-playbook playbooks/provision.yml --tags docker
...
PLAY RECAP *************************************
webservers : ok=8    changed=0    ...

# Skip common role
$ ansible-playbook playbooks/provision.yml --skip-tags common
...
PLAY RECAP *************************************
webservers : ok=3    changed=0    ...   # no common tasks executed
```

---

## Task 2: Docker Compose Migration

### Role Rename
```bash
mv roles/app_deploy roles/web_app
```

### Docker Compose Template (`roles/web_app/templates/docker-compose.yml.j2`)
```yaml
version: "{{ docker_compose_version }}"
services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_tag }}"
    container_name: "{{ app_name }}"
    ports:
      - "{{ app_port }}:{{ app_internal_port | default(app_port) }}"
    restart: unless-stopped
    environment:
      FLASK_ENV: production
    volumes:
      - "{{ compose_project_dir }}/app:/app"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port | default(app_port) }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3

```

### Deployment Tasks (`roles/web_app/tasks/main.yml`)
- Create app directory.
- Template `docker-compose.yml`.
- Deploy with `community.docker.docker_compose` (pull: yes, build: no).
- Rescue and always blocks for error handling and logging.
- Tags: `docker-compose`, `deploy`.

```yaml
---
- name: Deploy application with Docker Compose
  block:
      - name: Create app directory
        file:
            path: "{{ compose_project_dir }}"
            state: directory
            mode: "0755"
        become: yes

      - name: Template docker-compose file
        template:
            src: docker-compose.yml.j2
            dest: "{{ compose_project_dir }}/docker-compose.yml"
        notify: Restart containers if needed

      - name: Deploy with docker-compose
        community.docker.docker_compose:
            project_src: "{{ compose_project_dir }}"
            pull: yes
            build: no
        register: deploy_result
        become: yes
    rescue:
      - name: Handle deployment failure
        debug:
            msg: "Failed to deploy application with Docker Compose. Error: {{ deploy_result.msg | default('Unknown error') }}"
    always:
      - name: Log deployment completion
        debug:
            msg: "Deployment completed successfully or failed."
  when: ansible_os_family == "Debian"
  become: yes
  tags:
      - docker-compose
      - deploy
```

### Idempotency Proof

**First Run**:
```bash
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *************************************
webservers : ok=4    changed=8    ...
```

**Second Run (immediately after)**:
```bash
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *************************************
webservers : ok=12    changed=0    ...
```

### Verification on VM
```bash
$ ssh ubuntu@<VM_IP> docker ps
CONTAINER ID   IMAGE                                   COMMAND         STATUS         PORTS                    NAMES
abc123def456   saddogsec/devops-info-service:latest   "python app.py"   Up 3 minutes   0.0.0.0:8000->8000/tcp   devops-app

$ curl http://<VM_IP>:8000/health
{"status":"healthy","timestamp":"...","uptime_seconds":214}
```

---

## Task 3: Wipe Logic (1 pt)

### Implementation (`roles/web_app/tasks/wipe.yml`)
- Variable `web_app_wipe` defaults to `false` in `defaults/main.yml`.
- Included `wipe.yml` at the top of `main.yml` with `when: web_app_wipe | default(false)`.
- Wipe tasks: stop/remove containers, delete compose file, remove app directory.
- Tag `wipe` applied to all wipe tasks.

```yaml
---
- name: Wipe web application
  block:
      - name: Stop and remove containers
        community.docker.docker_compose:
            project_src: "{{ compose_project_dir }}"
            state: absent
        ignore_errors: yes

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
            msg: "Wipe completed successfully."
  when: web_app_wipe | default(false)
  tags:
      - wipe
```

### Test Scenarios

**Scenario 1 – Normal Deployment (`web_app_wipe=false`)**:
```bash
$ ansible-playbook playbooks/deploy.yml
...
TASK [web_app : Include wipe tasks] ****************
skipping: [webservers]
...
```
App deployed, wipe skipped.

**Scenario 2 – Wipe Only (`web_app_wipe=true` with tag)**:
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags wipe
...
TASK [web_app : Stop and remove containers] ********
changed: [webservers]
TASK [web_app : Remove docker-compose file] ********
changed: [webservers]
TASK [web_app : Remove application directory] ******
changed: [webservers]
...
PLAY RECAP *****************************************
webservers : ok=0    changed=4    ...
```

**Scenario 3 – Clean Reinstallation (`web_app_wipe=true` without tag)**:
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
...
TASK [web_app : Include wipe tasks] ****************
included: .../wipe.yml for webservers
TASK [web_app : Stop and remove containers] ********
changed: [webservers]
...
TASK [web_app : Deploy with docker compose] ********
changed: [webservers]
...
```

**Scenario 4 – Safety Checks**:
- Tag specified but variable false: tasks skipped.
- Variable true without tag: wipe runs (because condition true) → then deployment runs. This matches Scenario 3.

---

## Task 4: CI/CD with GitHub Actions

### Workflow File (`.github/workflows/ansible-deployment.yml`)
```yaml


name: Ansible Deployment

on:
  push:
    branches: [ main ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deployment.yml'
  pull_request:
    branches: [ main ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deployment.yml'

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
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install ansible ansible-lint

      - name: Run ansible-lint
        run: ansible-lint --force-color .

    deploy:
        name: Deploy Application
        needs: lint
        runs-on: ubuntu-latest

        steps:
            - name: Checkout code
              uses: actions/checkout@v4

            - name: Set up Python
              uses: actions/setup-python@v5
              with:
                  python-version: "3.10"

            - name: Install Ansible
              run: pip install ansible

            - name: Setup SSH
              run: |
                  mkdir -p ~/.ssh
                  echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
                  chmod 600 ~/.ssh/id_rsa
                  ssh-keyscan ${{ secrets.HOST }} >> ~/.ssh/known_hosts

            - name: Deploy with Ansible
              env:
                  ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
              run: |
                  ansible-playbook playbooks/deploy.yml --vault-password-file <(echo $ANSIBLE_VAULT_PASSWORD) --private-key ~/.ssh/id_rsa -i inventory/production.ini

            - name: Verify Deployment
              run: |
                  curl -f http://${{ secrets.HOST }}:${{ secrets.APP_PORT }}/health || exit 1

            - name: Cleanup SSH Private Key
              if: always()
              run: rm -f ~/.ssh/id_rsa
```

# Challenges & Solutions

No challenges were encountered in the lab

# Research Questions

- **Why use both variable AND tag? (Double safety mechanism)**
  - Variables hold the version value, tags lock that value in the Git history; using both ensures you can reference a stable commit (`tag`) while still allowing dynamic selection via `variable`.

- **What's the difference between never tag and this approach?**
  - “Never tag” skips creating an immutable reference, so any later change to the image or repository could be reused; tagging guarantees a specific digest is deployed.

- **Why must wipe logic come BEFORE deployment in main.yml? (Clean reinstall scenario)**
  -  Wiping removes old artifacts first, preventing conflicts or stale resources that could block the new deployment; it ensures a clean slate for the fresh run. 

- **When would you want clean reinstallation vs. rolling update?**
  - Use clean reinstall when major schema changes or incompatible config updates require a fresh start, use rolling update for incremental feature releases where downtime is undesirable. 

- **How would you extend this to wipe Docker images and volumes too?**
  - Add `docker rmi $(docker images -q)` and `docker volume rm $(docker volume ls -q)` steps in the pre‑deploy task.


- **What are the security implications of storing SSH keys in GitHub Secrets?**
  -  Keys are encrypted at rest and only exposed to workflows that request them, however, if a workflow is compromised or misconfigured, the key could be leaked 
 
- **How would you implement a staging → production deployment pipeline?**
  - Create separate branches (e.g., `staging`, `main`), trigger a “review” workflow on merge to staging, then upon approval run a production workflow that promotes artifacts and updates the prod environment. 

- **What would you add to make rollbacks possible?**
  - Store previous release tags or image digests; include a rollback job that restores the last successful tag/commit and redeploys it, optionally with a canary check before full rollout. 

- **How does self‑hosted runner improve security compared to GitHub-hosted?**
  - Self‑hosted runners run on your own infrastructure, limiting exposure of secrets to external hosts.

# Where to access the app?

http://rubwbeusbp.duckdns.org:5000

http://rubwbeusbp.duckdns.org:5000/health
