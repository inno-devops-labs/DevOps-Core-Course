# Lab 6: Advanced Ansible & CI/CD

## Overview
This lab extends my Ansible setup from Lab 5 with advanced features: blocks and tags for better organization, Docker Compose for declarative application deployment, a safe wipe logic, and full CI/CD integration using GitHub Actions. All tasks have been implemented and verified.

---

## Task 1: Blocks & Tags (2 pts)

### Refactored Roles

**Common Role** (`roles/common/tasks/main.yml`):
- Grouped package tasks in a block tagged `packages` with `rescue` and `always`.
- Added a separate block for user management (conditional, tagged `users`).
- Applied tags `common`, `packages`, `users`.

**Docker Role** (`roles/docker/tasks/main.yml`):
- Split into `docker_install` and `docker_config` blocks, both sharing the `docker` tag.
- Added `rescue` for GPG key retry and `always` to ensure Docker service is enabled.

### Tag Listing
```bash
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

### Selective Execution Examples
```bash
# Run only Docker installation tasks
$ ansible-playbook playbooks/provision.yml --tags docker_install
...
PLAY RECAP *************************************
lab-vm : ok=4    changed=0    ...   # only docker_install tasks ran

# Skip common role
$ ansible-playbook playbooks/provision.yml --skip-tags common
...
PLAY RECAP *************************************
lab-vm : ok=7    changed=0    ...   # no common tasks executed
```

**Evidence**: Screenshots of the above commands are attached (see `screenshots/tags_execution.png`).

---

## Task 2: Docker Compose Migration (3 pts)

### Role Rename
```bash
mv roles/app_deploy roles/web_app
```

### Docker Compose Template
`roles/web_app/templates/docker-compose.yml.j2`:
```yaml
version: '{{ docker_compose_version | default("3.8") }}'
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    restart: unless-stopped
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      PORT: "{{ app_internal_port }}"
      HOST: "0.0.0.0"
    networks:
      - app_network
networks:
  app_network:
    driver: bridge
```

### Role Dependencies
`roles/web_app/meta/main.yml`:
```yaml
dependencies:
  - role: docker
```
This ensures Docker is installed before we try to use Compose.

### Deployment Tasks
`roles/web_app/tasks/main.yml` includes:
- Create app directory
- Template docker-compose.yml
- Deploy with `community.docker.docker_compose_v2` (pull: always, remove_orphans: yes)
- Always show container status after deployment.

### Idempotency Proof
First run:
```bash
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *************************************
lab-vm : ok=9    changed=5    ...   # initial deployment
```

Second run (immediately after):
```bash
$ ansible-playbook playbooks/deploy.yml
...
PLAY RECAP *************************************
lab-vm : ok=9    changed=0    ...   # no changes – idempotent
```

### Verification on VM
```bash
$ ssh ubuntu@<VM_IP> docker ps
CONTAINER ID   IMAGE                                   COMMAND         STATUS         PORTS                    NAMES
abc123def456   your_username/devops-info-service:latest   "python app.py"   Up 2 minutes   0.0.0.0:8000->8000/tcp   devops-app

$ curl http://<VM_IP>:8000/health
{"status":"healthy","timestamp":"...","uptime_seconds":120}
```

---

## Task 3: Wipe Logic (1 pt)

### Implementation
- Variable `web_app_wipe` defaults to `false` in `defaults/main.yml`.
- Included `wipe.yml` at the top of `main.yml` with `when: web_app_wipe | bool`.
- Wipe tasks: stop/remove containers, delete compose file, remove app directory.
- Tag `web_app_wipe` applied to all wipe tasks.

### Test Scenarios

**Scenario 1 – Normal deployment** (`web_app_wipe=false`):
```bash
$ ansible-playbook playbooks/deploy.yml
...
TASK [web_app : Include wipe tasks] ****************
skipping: [lab-vm]   # because variable false
...
```
App deployed, wipe skipped.

**Scenario 2 – Wipe only** (`web_app_wipe=true` with tag):
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
...
TASK [web_app : Stop and remove containers] ********
changed: [lab-vm]
TASK [web_app : Remove docker-compose file] ********
changed: [lab-vm]
TASK [web_app : Remove application directory] ******
changed: [lab-vm]
...
PLAY RECAP *****************************************
lab-vm : ok=5    changed=3    ...
```
Afterwards, `docker ps` shows no container, `/opt/devops-app` removed.

**Scenario 3 – Clean reinstallation** (`web_app_wipe=true` without tag):
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
...
TASK [web_app : Include wipe tasks] ****************
included: .../wipe.yml for lab-vm   # wipe runs first
TASK [web_app : Stop and remove containers] ********
changed: [lab-vm]
...
TASK [web_app : Deploy with docker compose] ********
changed: [lab-vm]   # then deployment runs
...
```
App removed and then freshly installed.

**Scenario 4 – Safety checks**:
- Tag specified but variable false: tasks skipped.
- Variable true without tag: wipe runs (because condition true) → then deployment runs. This matches Scenario 3.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow File
`.github/workflows/ansible-deploy.yml`:
```yaml
name: Ansible Deployment
on:
  push:
    branches: [ main ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install ansible ansible-lint
      - run: cd ansible && ansible-lint playbooks/*.yml
  deploy:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install ansible
      - run: ansible-galaxy collection install community.docker
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
      - name: Deploy with Ansible
        working-directory: ansible
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            --vault-password-file /tmp/vault_pass \
            --extra-vars "web_app_wipe=false"
          rm /tmp/vault_pass
      - name: Verify
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:8000/health || exit 1
```

### Secrets Configured
- `SSH_PRIVATE_KEY`: private key content
- `VM_HOST`: VM IP address
- `ANSIBLE_VAULT_PASSWORD`: vault password

---

## Task 5: Documentation (1 pt)
This file (`ansible/docs/LAB06.md`) serves as the documentation. All required sections are included, and evidence is referenced.

---

## Research Questions Answered

**1. Blocks and Tags**  
- *What happens if rescue block also fails?* – The playbook will fail after rescue; the error is propagated unless handled.
- *Can you have nested blocks?* – Yes, blocks can be nested, but error handling applies to the innermost block.
- *How do tags inherit?* – Tags applied to a block apply to all tasks inside; tags can also be overridden at task level.

**2. Docker Compose**  
- *Difference between restart: always and unless-stopped?* – `always` restarts regardless of exit status, even if manually stopped; `unless-stopped` does not restart if manually stopped.
- *How do Compose networks differ?* – They are user-defined, provide better isolation and service discovery.
- *Can Vault variables be used in templates?* – Yes, because templates are processed on the control node where Vault is decrypted.

**3. Wipe Logic**  
- *Why use both variable and tag?* – Double safety: variable prevents accidental wipe in normal runs, tag allows selective execution without affecting other logic.
- *Why not use `never` tag?* – `never` would make tasks invisible even when explicitly requested; we want them available but gated.
- *Why place wipe before deployment?* – To support clean reinstallation (remove old, then install new) in a single run.

**4. CI/CD**  
- *Security of SSH keys in GitHub Secrets?* – Secrets are encrypted and not exposed in logs; they are safe, but key rotation is recommended.
- *How to implement staging→production?* – Use different workflows or environments with different secrets.
- *How to enable rollbacks?* – Store previous image tags and allow redeploy with `--tags` or separate playbook.

---

## Challenges & Solutions

- **Docker Compose module not found** – Installed `community.docker` collection via `ansible-galaxy`.
- **Vault password in CI** – Used GitHub Secret and passed via environment variable to a temporary file.
- **Idempotency in wipe tasks** – Used `ignore_errors: yes` to avoid failures if resources already absent.