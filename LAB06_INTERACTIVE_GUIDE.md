# Lab 06 Interactive Guide (Beginner + Yandex Cloud)

This guide is built for your current repository and current Lab 06 requirements.
Goal: learn what Terraform/Ansible/CI-CD are and finish Lab 06 while doing it.

You will produce:
- Updated Ansible code in `ansible/`
- CI workflow in `.github/workflows/`
- Final submission report in `ansible/docs/LAB06.md`

---

## 0. Zero-BS Mental Model (What These Tools Are)

### Terraform
Terraform is for **creating infrastructure** (VM, subnet, firewall, etc.) from code.
- Think: "Give me a server in Yandex Cloud."
- Input: `.tf` files in `terraform/`
- Output: real cloud resources + state file

### Ansible
Ansible is for **configuring and deploying software** on existing servers.
- Think: "Install Docker, deploy app, verify health endpoint."
- Input: YAML playbooks + roles in `ansible/`
- Output: configured VM and running application

### GitHub Actions
GitHub Actions is for **automation on push/PR**.
- Think: "Whenever I push Ansible changes, lint and deploy automatically."
- Input: workflow YAML in `.github/workflows/`
- Output: automated checks/deploy pipeline

### How they fit together in your course
1. Terraform (Lab 4): create VM in Yandex Cloud
2. Ansible (Lab 5/6): configure VM + deploy app
3. CI/CD (Lab 6): automate Ansible in GitHub Actions

---

## 1. Prerequisites Check (Do This First)

### 1.1 Confirm repo and branch

Run:
```bash
cd /home/eugene/IU/DevOps/DevOps-Core-Course
git checkout -b lab06
```

What these commands do:
- `cd ...`: moves terminal to project root.
- `git checkout -b lab06`: creates and switches to branch `lab06`.

### 1.2 Confirm tools installed

Run:
```bash
ansible --version
ansible-lint --version
docker --version
terraform --version
yc --version
```

Why:
- You need Ansible/ansible-lint for Lab 6.
- Docker for local validation if needed.
- Terraform/yc are useful to check and recover VM info in Yandex Cloud.

If `ansible-lint` is missing:
```bash
python3 -m pip install --user ansible-lint
```

### 1.3 Confirm your VM is reachable (Yandex Cloud)

Your inventory file is:
- `ansible/inventory/hosts.ini`

Check IP/user there and test:
```bash
ansible -i ansible/inventory/hosts.ini webservers -m ping
```

What it does:
- Uses Ansible ping module (not ICMP ping) to verify SSH + Python access.

If ping fails:
- Check Yandex VM is running.
- Check security group allows port 22.
- Check `ansible_user` and SSH key.

---

## 2. Understand Current Structure Before Editing

Current relevant tree:
```text
ansible/
  ansible.cfg
  inventory/hosts.ini
  group_vars/all.yml
  playbooks/
    provision.yml
    deploy.yml
    site.yml
  roles/
    common/
    docker/
    app_deploy/   <- will be renamed to web_app in Lab 6
```

### What each part means
- `playbooks/`: entry points (`provision.yml`, `deploy.yml`)
- `roles/`: reusable modules of tasks
- `group_vars/all.yml`: shared variables (currently vault-encrypted)
- `ansible.cfg`: default inventory, vault password file, SSH behavior

---

## 3. Task 1 (Blocks + Tags) - Refactor `common` and `docker`

Lab requires grouping tasks with `block`, adding `rescue`/`always`, and tag strategy.

## 3.1 Edit `ansible/roles/common/tasks/main.yml`

Replace file with:
```yaml
---
- name: Common role | Package management with recovery
  block:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: "{{ common_apt_cache_valid_time }}"

    - name: Install common packages
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present

  rescue:
    - name: Recover apt cache update with fix-missing
      ansible.builtin.command: apt-get update --fix-missing
      changed_when: true

    - name: Retry common packages installation after recovery
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present

  always:
    - name: Log completion of common package block
      ansible.builtin.copy:
        dest: /tmp/ansible-common-packages.log
        content: "Common package block completed at {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"

  become: true
  tags:
    - common
    - packages

- name: Common role | User/timezone related tasks
  block:
    - name: Read current timezone
      ansible.builtin.command: timedatectl show --property=Timezone --value
      register: common_current_timezone
      changed_when: false
      when: common_configure_timezone

    - name: Set system timezone
      ansible.builtin.command: timedatectl set-timezone "{{ common_timezone }}"
      when:
        - common_configure_timezone
        - common_current_timezone.stdout != common_timezone

  always:
    - name: Log completion of common user/timezone block
      ansible.builtin.copy:
        dest: /tmp/ansible-common-users.log
        content: "Common user/timezone block completed at {{ ansible_date_time.iso8601 }}\n"
        mode: "0644"

  become: true
  tags:
    - common
    - users
```

Why this satisfies lab:
- Uses `block/rescue/always`
- Adds `packages` and `users` tags
- Recovery command for apt failures
- Logs block completion in `/tmp`

## 3.2 Edit `ansible/roles/docker/tasks/main.yml`

Replace file with:
```yaml
---
- name: Docker role | Install Docker packages with retry logic
  block:
    - name: Install Docker apt prerequisites
      ansible.builtin.apt:
        name: "{{ docker_apt_prerequisites }}"
        state: present
        update_cache: true
        cache_valid_time: 3600

    - name: Create Docker apt keyring directory
      ansible.builtin.file:
        path: "{{ docker_keyring_dir }}"
        state: directory
        mode: "0755"

    - name: Add Docker GPG key
      ansible.builtin.get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: "{{ docker_keyring_path }}"
        mode: "0644"

    - name: Add Docker apt repository
      ansible.builtin.apt_repository:
        repo: "{{ docker_apt_repo }}"
        state: present
        filename: docker
      register: docker_repository

    - name: Refresh apt cache after repository change
      ansible.builtin.apt:
        update_cache: true
      when: docker_repository.changed

    - name: Install Docker engine packages
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
      notify: restart docker

  rescue:
    - name: Wait before retry when docker repo setup fails
      ansible.builtin.pause:
        seconds: 10

    - name: Retry apt cache update after Docker key/repo issue
      ansible.builtin.apt:
        update_cache: true

    - name: Retry Docker engine package installation
      ansible.builtin.apt:
        name: "{{ docker_packages }}"
        state: present
      notify: restart docker

  always:
    - name: Ensure Docker service is enabled and running
      ansible.builtin.service:
        name: "{{ docker_service_name }}"
        state: started
        enabled: true

  become: true
  tags:
    - docker
    - docker_install

- name: Docker role | Docker user + Python SDK config
  block:
    - name: Add users to docker group
      ansible.builtin.user:
        name: "{{ item }}"
        groups: docker
        append: true
      loop: "{{ docker_users }}"
      when: docker_users | length > 0

    - name: Install python Docker bindings
      ansible.builtin.apt:
        name: "{{ docker_python_packages }}"
        state: present

  become: true
  tags:
    - docker
    - docker_config
```

Why:
- `docker_install` tag groups install path
- `docker_config` tag groups post-install config
- rescue includes 10-second wait + retry
- always ensures service state

## 3.3 Tag role calls in playbook

Edit `ansible/playbooks/provision.yml`:
```yaml
---
- name: Provision web servers
  hosts: webservers
  become: true
  roles:
    - role: common
      tags:
        - common
    - role: docker
      tags:
        - docker
```

Why:
- Enables `--skip-tags common` and role-level selection cleanly.

## 3.4 Test Task 1

Run:
```bash
cd ansible
ansible-playbook playbooks/provision.yml --list-tags
ansible-playbook playbooks/provision.yml --tags "docker"
ansible-playbook playbooks/provision.yml --skip-tags "common"
ansible-playbook playbooks/provision.yml --tags "packages"
ansible-playbook playbooks/provision.yml --tags "docker_install" --check
```

Command explanations:
- `--list-tags`: prints tags available in playbook.
- `--tags "docker"`: run only tasks tagged `docker`.
- `--skip-tags "common"`: run everything except `common`.
- `--check`: dry-run mode; shows what would change.

Checkpoint:
- You can selectively run parts of provisioning.
- You can capture outputs/screenshots for `ansible/docs/LAB06.md`.

---

## 4. Task 2 (Docker Compose Migration + Role Dependency)

You currently have role `app_deploy` with `docker_container`.
Lab 6 wants Docker Compose + role rename to `web_app`.

## 4.1 Rename role

Run:
```bash
cd ansible/roles
mv app_deploy web_app
```

What this command does:
- Renames folder, preserving all files/history in git as move detection.

## 4.2 Add role dependency metadata

Create `ansible/roles/web_app/meta/main.yml`:
```yaml
---
dependencies:
  - role: docker
```

Why:
- If `web_app` runs, `docker` role runs first automatically.

## 4.3 Create Compose template

Create `ansible/roles/web_app/templates/docker-compose.yml.j2`:
```yaml
version: "{{ docker_compose_version }}"

services:
  {{ app_name }}:
    image: "{{ docker_image }}:{{ docker_tag }}"
    container_name: "{{ app_name }}"
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      HOST: "{{ app_host }}"
      PORT: "{{ app_internal_port }}"
      APP_ENV: "{{ app_env }}"
      APP_SECRET_KEY: "{{ app_secret_key }}"
    restart: unless-stopped
```

Why:
- Jinja2 template renders environment-specific compose file.
- Keeps deployment declarative and repeatable.

## 4.4 Update web_app defaults

Replace `ansible/roles/web_app/defaults/main.yml` with:
```yaml
---
# App identity
app_name: devops-info
app_env: production
app_host: "0.0.0.0"

# Container image
docker_image: "your_dockerhub_username/devops-info-service"
docker_tag: latest

# Port mapping
app_port: 5000
app_internal_port: 5000

# Compose project
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"

# Wipe logic safety switch (Task 3)
web_app_wipe: false

# Secret must come from Vault/group_vars
app_secret_key: "change-me-in-vault"
```

Why:
- Non-sensitive defaults stay in role.
- Sensitive value (`app_secret_key`) should be overridden from Vault.

## 4.5 Implement main deployment tasks with compose + tags

Replace `ansible/roles/web_app/tasks/main.yml` with:
```yaml
---
- name: Include wipe logic tasks
  ansible.builtin.include_tasks: wipe.yml
  tags:
    - web_app_wipe

- name: Deploy application with Docker Compose
  block:
    - name: Create compose project directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: directory
        mode: "0755"

    - name: Render docker-compose.yml from template
      ansible.builtin.template:
        src: docker-compose.yml.j2
        dest: "{{ compose_project_dir }}/docker-compose.yml"
        mode: "0644"

    - name: Ensure Docker Hub login for pulling private image (if needed)
      community.docker.docker_login:
        registry_url: "{{ docker_registry_url | default('https://index.docker.io/v1/') }}"
        username: "{{ dockerhub_username }}"
        password: "{{ dockerhub_password }}"
      when:
        - dockerhub_username is defined
        - dockerhub_password is defined
        - dockerhub_username | length > 0
        - dockerhub_password | length > 0
      no_log: true

    - name: Deploy stack with docker compose v2
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        pull: always
        state: present
      register: web_app_compose_result

    - name: Wait for app TCP port
      ansible.builtin.wait_for:
        host: "127.0.0.1"
        port: "{{ app_port }}"
        timeout: 60
        delay: 2

    - name: Verify health endpoint
      ansible.builtin.uri:
        url: "http://127.0.0.1:{{ app_port }}/health"
        method: GET
        status_code: 200
      changed_when: false

  rescue:
    - name: Print compose failure debug details
      ansible.builtin.debug:
        var: web_app_compose_result

    - name: Fail explicitly after rescue logging
      ansible.builtin.fail:
        msg: "Docker Compose deployment failed. Check docker-compose.yml and image availability."

  tags:
    - app_deploy
    - compose
    - web_app
```

Why:
- Uses Compose module (Lab requirement).
- Adds `app_deploy` and `compose` tags.
- Adds block+rescue flow for controlled failure.

## 4.6 Create wipe task file now (needed by include)

Create `ansible/roles/web_app/tasks/wipe.yml`:
```yaml
---
- name: Wipe web application deployment
  block:
    - name: Stop and remove compose stack
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      ignore_errors: true

    - name: Remove rendered docker-compose.yml
      ansible.builtin.file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent

    - name: Remove compose project directory
      ansible.builtin.file:
        path: "{{ compose_project_dir }}"
        state: absent

    - name: Report wipe completion
      ansible.builtin.debug:
        msg: "Wipe completed for app {{ app_name }}"

  when: web_app_wipe | default(false) | bool
  tags:
    - web_app_wipe
```

## 4.7 Update deploy playbook role name

Replace `ansible/playbooks/deploy.yml`:
```yaml
---
- name: Deploy application
  hosts: webservers
  become: true
  vars_files:
    - ../group_vars/all.yml
  roles:
    - role: web_app
      tags:
        - web_app
        - app_deploy
```

## 4.8 Install required collection

Run:
```bash
cd /home/eugene/IU/DevOps/DevOps-Core-Course/ansible
ansible-galaxy collection install community.docker
```

What it does:
- Installs `community.docker` modules used by `docker_login` and `docker_compose_v2`.

## 4.9 Test Task 2

Run:
```bash
ansible-playbook playbooks/deploy.yml
ansible-playbook playbooks/deploy.yml
```

Why run twice:
- 1st run creates/updates resources.
- 2nd run should be mostly `ok` (idempotency evidence).

Verify on VM:
```bash
ssh ubuntu@<YOUR_VM_IP> "docker ps"
ssh ubuntu@<YOUR_VM_IP> "docker compose -f /opt/devops-info/docker-compose.yml ps"
curl http://<YOUR_VM_IP>:5000/health
```

---

## 5. Task 3 (Wipe Logic with Double Safety)

Already implemented above via:
- `web_app_wipe` variable (defaults `false`)
- `web_app_wipe` tag
- `wipe.yml` included before deploy block

This is "double gate":
1. Tag must be explicitly selected OR full run without tag filter.
2. Variable must be true for destructive wipe actions.

## 5.1 Test required scenarios

Scenario 1: normal deploy (wipe should not run)
```bash
ansible-playbook playbooks/deploy.yml
```

Scenario 2: wipe only
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```

Scenario 3: clean reinstall (wipe then deploy)
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```

Scenario 4a: tag present but variable false
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```

How to read result:
- In 4a, wipe tasks should be skipped due to `when`.
- In 3, wipe runs first then deployment runs.

---

## 6. Task 4 (CI/CD with GitHub Actions)

## 6.1 Create workflow file

Create `.github/workflows/ansible-deploy.yml`:
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
      - '.github/workflows/ansible-deploy.yml'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install lint dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ansible ansible-lint

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    name: Deploy via Ansible
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Ansible and Docker collection
        run: |
          pip install ansible
          ansible-galaxy collection install community.docker

      - name: Configure SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H "${{ secrets.VM_HOST }}" >> ~/.ssh/known_hosts

      - name: Create dynamic inventory override
        run: |
          cat > ansible/inventory/hosts.ci.ini <<EOF
          [webservers]
          ci-target ansible_host=${{ secrets.VM_HOST }} ansible_user=${{ secrets.VM_USER }}
          [webservers:vars]
          ansible_python_interpreter=/usr/bin/python3
          EOF

      - name: Deploy playbook
        env:
          ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
        run: |
          cd ansible
          printf "%s" "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
          ansible-playbook -i inventory/hosts.ci.ini playbooks/deploy.yml \
            --vault-password-file /tmp/vault_pass \
            --tags "app_deploy"
          rm -f /tmp/vault_pass

      - name: Verify deployment endpoint
        run: |
          sleep 10
          curl -f "http://${{ secrets.VM_HOST }}:5000/health"
```

## 6.2 Configure GitHub Secrets

In GitHub repo settings, add:
- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

Explanation:
- `SSH_PRIVATE_KEY`: key for VM SSH access from runner.
- `VM_HOST`: Yandex VM public IP/DNS.
- `VM_USER`: usually `ubuntu`.
- `ANSIBLE_VAULT_PASSWORD`: decrypts `group_vars/all.yml`.

## 6.3 Add workflow badge

Add to top of `README.md`:
```markdown
[![Ansible Deployment](https://github.com/<YOUR_USER>/<YOUR_REPO>/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/<YOUR_USER>/<YOUR_REPO>/actions/workflows/ansible-deploy.yml)
```

Why:
- Lab requires visible CI status proof.

---

## 7. Task 5 (Write Submission Report)

Create `ansible/docs/LAB06.md` with required structure from lab file.

Use this command to start:
```bash
cp labs/lab06.md /tmp/lab06-reference.md
```

Then create your own concise report file with:
- Task 1 evidence (tags, rescue, list-tags output)
- Task 2 evidence (compose deploy + idempotency)
- Task 3 evidence (all 4 wipe scenarios)
- Task 4 evidence (workflow logs + badge)
- research question answers

Tip:
- Paste sanitized terminal snippets as fenced code blocks.
- Put screenshots under `ansible/docs/screenshots/` and reference them in markdown.

---

## 8. Command Glossary (Everything Used Above)

`git checkout -b lab06`
- Creates and switches to new git branch for Lab 6 changes.

`ansible -i ... webservers -m ping`
- Verifies Ansible can SSH and run Python module on targets.

`ansible-playbook ... --list-tags`
- Shows all tags available in a playbook run.

`ansible-playbook ... --tags X`
- Runs only tasks tagged `X`.

`ansible-playbook ... --skip-tags X`
- Runs tasks except those tagged `X`.

`ansible-playbook ... --check`
- Dry run mode (no actual changes where possible).

`ansible-galaxy collection install community.docker`
- Installs community module set for Docker-related Ansible tasks.

`ssh ubuntu@<ip> "docker ps"`
- Remote check for running containers on VM.

`curl http://<ip>:5000/health`
- Verifies app health endpoint from your machine.

---

## 9. File Glossary (Everything You Touch)

`ansible/playbooks/provision.yml`
- Entry point for base server setup (`common`, `docker`).

`ansible/playbooks/deploy.yml`
- Entry point for app deployment (`web_app` role).

`ansible/roles/common/tasks/main.yml`
- OS-level base tasks (packages/timezone) with block+rescue+always.

`ansible/roles/docker/tasks/main.yml`
- Docker engine installation/configuration with block+rescue+always.

`ansible/roles/web_app/meta/main.yml`
- Role dependency declaration (`docker` first).

`ansible/roles/web_app/defaults/main.yml`
- Default non-sensitive app variables and wipe toggle.

`ansible/roles/web_app/templates/docker-compose.yml.j2`
- Compose template rendered per environment/vars.

`ansible/roles/web_app/tasks/main.yml`
- Main deployment flow (include wipe + deploy + checks).

`ansible/roles/web_app/tasks/wipe.yml`
- Controlled cleanup logic (`web_app_wipe` tag + var gate).

`.github/workflows/ansible-deploy.yml`
- CI pipeline: lint -> deploy -> verify.

`ansible/docs/LAB06.md`
- Final lab submission file your teacher grades.

---

## 10. Final Checklist (Before Commit)

- [ ] `common` and `docker` roles use block/rescue/always + tags
- [ ] `app_deploy` renamed to `web_app`
- [ ] Compose template exists and deploys app
- [ ] `web_app` has dependency on `docker`
- [ ] Wipe logic implemented with variable + tag
- [ ] All 4 wipe test scenarios executed and captured
- [ ] GitHub Actions workflow runs and passes
- [ ] ansible-lint passes
- [ ] Badge added to README
- [ ] `ansible/docs/LAB06.md` complete with evidence + research answers

Commit commands:
```bash
git add ansible .github/workflows README.md ansible/docs/LAB06.md LAB06_INTERACTIVE_GUIDE.md
git commit -m "Add interactive Lab 06 guide and complete advanced Ansible tasks"
git push -u origin lab06
```

---

## 11. If You Get Stuck (Fast Debug Path)

Run these in order and read errors top-to-bottom:
```bash
cd ansible
ansible-playbook playbooks/provision.yml -vv
ansible-playbook playbooks/deploy.yml -vv
ansible-lint playbooks/*.yml
```

Most common issues:
- Wrong Docker image name/tag
- Vault password mismatch
- SSH key/user mismatch
- VM security group missing app port (5000)
- App listens on different internal port than compose config

