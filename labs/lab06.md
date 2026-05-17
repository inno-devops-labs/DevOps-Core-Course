# Lab 6 — Advanced Ansible & CI/CD

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Ansible%20%26%20CI%2FCD-blue)
![points](https://img.shields.io/badge/points-10%2B2.5-orange)
![tech](https://img.shields.io/badge/tech-Ansible%20|%20Docker%20Compose%20|%20GitHub%20Actions-informational)

> Enhance your Ansible automation with advanced features including blocks, tags, Docker Compose, role dependencies, wipe logic, and CI/CD integration.

## Overview

Build on Lab 5 by enhancing your Ansible automation with production-ready features. You'll refactor roles with blocks and tags, upgrade to Docker Compose, implement safe cleanup logic, and fully automate deployments with CI/CD.

**What You'll Learn:**
- Blocks for error handling and task grouping
- Tags for selective Ansible execution
- Docker Compose templating with Jinja2
- Role dependencies and execution order
- Safe wipe logic with double-gating (variable + tag)
- GitHub Actions for Ansible automation
- Multi-app deployment patterns (Bonus)

**Tech Stack:** Ansible 2.16+ | Docker Compose v2 | GitHub Actions | Jinja2

**Prerequisites:** Lab 5 completed (Ansible roles, playbooks, Vault), containerized app from Lab 2, GitHub Actions knowledge from Lab 3

---

## Tasks

### Task 1 — Refactor with Blocks & Tags (2 pts)

#### 1.1 Understanding Blocks

Blocks allow you to:
- **Group tasks** logically (e.g., all Docker installation tasks)
- **Apply directives** once to multiple tasks (when, become, tags)
- **Handle errors** with rescue and always sections
- **Improve readability** by showing task relationships

**Example Block Pattern:**
```yaml
- name: Install package with error handling
  block:
    - name: Update apt cache
      # task 1

    - name: Install package
      # task 2

  rescue:
    - name: Handle installation failure
      # runs only if block fails

  always:
    - name: Cleanup temp files
      # runs regardless of success/failure

  when: ansible_os_family == "Debian"
  become: true
  tags:
    - packages
```

#### 1.2 Understanding Tags

Tags enable selective execution:
```bash
# Run only tagged tasks
ansible-playbook provision.yml --tags "docker"

# Skip specific tags
ansible-playbook provision.yml --skip-tags "common"

# Multiple tags
ansible-playbook provision.yml --tags "packages,docker"

# List all available tags
ansible-playbook provision.yml --list-tags
```

#### 1.3 Refactor `common` Role

**File:** `roles/common/tasks/main.yml`

**Requirements:**
1. Group package installation tasks in a block with tag `packages`
2. Group user creation tasks in a block with tag `users`
3. Add error handling with rescue for apt cache update failures
4. Use always block to log completion

**Tag Strategy:**
- `packages` - all package installation tasks
- `users` - all user management tasks
- `common` - entire role (applied at role level)

**Hints:**
- Add rescue block that runs `apt-get update --fix-missing` on failure
- Use always block to create a log file in /tmp indicating completion
- Apply `become: true` at block level instead of per task

**Research Questions:**
- Q: What happens if rescue block also fails?
- Q: Can you have nested blocks?
- Q: How do tags inherit to tasks within blocks?

#### 1.4 Refactor `docker` Role

**File:** `roles/docker/tasks/main.yml`

**Requirements:**
1. Group Docker installation tasks in block with tag `docker_install`
2. Group Docker configuration tasks in block with tag `docker_config`
3. Add rescue block to retry apt update on GPG key failure
4. Use always block to ensure Docker service is enabled

**Additional Tags:**
- `docker` - entire role
- `docker_install` - installation only
- `docker_config` - configuration only

**Hints:**
- Docker GPG key addition may fail on first try (network timeout)
- Rescue block should wait 10 seconds and retry
- Always block should ensure Docker service is enabled and started

#### 1.5 Testing Blocks & Tags

**Test Commands:**
```bash
# Test provision with only docker
ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only across all roles
ansible-playbook playbooks/provision.yml --tags "packages"

# Check mode to see what would run
ansible-playbook playbooks/provision.yml --tags "docker" --check

# Run only docker installation tasks
ansible-playbook playbooks/provision.yml --tags "docker_install"
```

**Evidence Required:**
- Output showing selective execution with --tags
- Output showing error handling with rescue block triggered
- List of all available tags (--list-tags output)

---

### Task 2 — Upgrade to Docker Compose (3 pts)

#### 2.1 Why Docker Compose?

**Advantages over `docker run`:**
- **Declarative configuration** - define desired state, not commands
- **Multi-container management** - networks, volumes, dependencies
- **Environment variable management** - .env files, variable substitution
- **Easy updates** - change config file and recreate
- **Better for production** - consistent, reproducible deployments

#### 2.2 Rename Role

**Action Required:**
```bash
cd ansible/roles
mv app_deploy web_app
```

**Update all references:**
- Playbook imports: `roles/app_deploy` → `roles/web_app`
- Documentation: app_deploy → web_app
- Variable prefixes: Consider `web_app_*` for consistency

**Why rename?**
- `web_app` is more specific and descriptive
- Prepares for potential other app types (database_app, cache_app)
- Better aligns with wipe logic variable naming

#### 2.3 Create Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

**Requirements:**
1. Use Jinja2 templating for dynamic values
2. Define service name, image, ports, environment variables
3. Include restart policy
4. Use networks if needed
5. Support variable substitution for app-specific config

**Template Pattern:**
```yaml
version: '3.8'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      # Add environment variables here
      # Use Vault-encrypted secrets
    restart: unless-stopped
    # Add other configuration
```

**Variables to support:**
- `app_name` - service/container name (default: devops-app)
- `docker_image` - Docker Hub image
- `docker_tag` - image version (default: latest)
- `app_port` - host port (default: 8000)
- `app_internal_port` - container port (default: 8000)
- Environment variables for app configuration

**Research Questions:**
- Q: What's the difference between `restart: always` and `restart: unless-stopped`?
- Q: How do Docker Compose networks differ from Docker bridge networks?
- Q: Can you reference Ansible Vault variables in the template?

#### 2.4 Define Role Dependencies

**File:** `roles/web_app/meta/main.yml`

**Purpose:** Ensure Docker is installed before deploying web app.

**Pattern:**
```yaml
---
dependencies:
  - role: role_name
    # Optional variables to pass
    vars:
      var_name: value
```

**Requirements:**
1. Add `docker` role as dependency
2. Ensure correct execution order automatically
3. Document why dependency is needed

**Test:** Run only `web_app` role - Docker should install automatically:
```bash
ansible-playbook playbooks/deploy.yml
# Should automatically run docker role first
```

#### 2.5 Implement Docker Compose Deployment

**File:** `roles/web_app/tasks/main.yml`

**Requirements:**
1. Create application directory (e.g., /opt/{{ app_name }})
2. Template docker-compose.yml to the directory
3. Use `docker_compose` module (or `community.docker.docker_compose`)
4. Ensure idempotency (check if already running)
5. Add appropriate tags: `app_deploy`, `compose`

**Deployment Block Pattern:**
```yaml
- name: Deploy application with Docker Compose
  block:
    - name: Create app directory
      # Use file module

    - name: Template docker-compose file
      # Use template module

    - name: Deploy with docker-compose
      # Use docker_compose module
      # state: present (or up)

  rescue:
    - name: Handle deployment failure
      # Log error, optionally rollback

  tags:
    - app_deploy
    - compose
```

**Hints:**
- Install docker-compose Python library: `pip3 install docker-compose`
- Or use `community.docker` collection (requires installation)
- Set `pull: yes` to always get latest image
- Use `project_src` to specify directory with docker-compose.yml

**Research:**
- Look up `community.docker.docker_compose_v2` module
- Compare `state: present` vs other state options
- Understand `recreate` parameter options

#### 2.6 Variables Configuration

**File:** `group_vars/all.yml` (or role defaults)

**Required Variables:**
```yaml
# Application Configuration
app_name: devops-app
docker_image: your_dockerhub_username/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000

# Docker Compose Config
compose_project_dir: "/opt/{{ app_name }}"
docker_compose_version: "3.8"

# Secrets (use Vault)
app_secret_key: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

**Encrypt sensitive values:**
```bash
ansible-vault encrypt_string 'secret_value' --name 'app_secret_key'
```

#### 2.7 Testing Docker Compose Deployment

**Test Commands:**
```bash
# Full deployment
ansible-playbook playbooks/deploy.yml

# Check idempotency (run twice, second should show no changes)
ansible-playbook playbooks/deploy.yml
ansible-playbook playbooks/deploy.yml

# Verify on target VM
ssh user@vm_ip
docker ps
docker-compose -f /opt/devops-app/docker-compose.yml ps
curl http://localhost:8000
```

**Evidence Required:**
- Output showing Docker Compose deployment success
- Idempotency proof (second run shows "ok" not "changed")
- Application running and accessible
- Contents of templated docker-compose.yml

---

### Task 3 — Wipe Logic Implementation (1 pt)

#### 3.1 Understanding Wipe Logic

**Purpose:** Clean removal of deployed applications for:
- **Clean reinstallation** (wipe old → deploy new)
- Testing from fresh state
- Rolling back to clean slate
- Decommissioning applications
- Resource cleanup before upgrades

**Implementation Requirements:**
- ✅ Controlled by variable: `web_app_wipe: true`
- ✅ Gated by specific tag: `web_app_wipe`
- ❌ NOT using the special "never" tag
- Default behavior: wipe tasks do NOT run
- Explicit invocation required

#### 3.2 Create Wipe Tasks

**File:** `roles/web_app/tasks/wipe.yml`

**Requirements:**
1. Stop and remove containers (Docker Compose down)
2. Remove docker-compose.yml file
3. Remove application directory
4. Optionally remove Docker images (consider disk space)
5. Log wipe completion

**Implementation Pattern:**
```yaml
---
- name: Wipe web application
  block:
    - name: Stop and remove containers
      ...

    - name: Remove docker-compose file
      ...

    - name: Remove application directory
      ...

    - name: Log wipe completion
      debug:
        msg: "Application {{ app_name }} wiped successfully"

  when: ...
  tags:
    - web_app_wipe
```

**Key Points:**
- `when` condition checks variable (default: false)
- `tags` enables selective execution
- `ignore_errors` prevents failure if already clean
- `| bool` ensures proper boolean evaluation

#### 3.3 Include Wipe in Main Tasks

**File:** `roles/web_app/tasks/main.yml`

**Add at the beginning (before deployment tasks):**
```yaml
---
# Wipe logic runs first (when explicitly requested)
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags:
    - web_app_wipe

# Deployment tasks follow...
- name: Deploy application with Docker Compose
  block:
    # ... your deployment tasks
```

**Why at the beginning?**
- Enables clean reinstallation: wipe → deploy
- Logical flow: remove old → install new
- Tag isolation still prevents accidental wipe during normal deployment
- Supports use case: `ansible-playbook deploy.yml -e "web_app_wipe=true"`

#### 3.4 Configure Wipe Variable

**File:** `roles/web_app/defaults/main.yml`

**Add:**
```yaml
# Wipe Logic Control
web_app_wipe: false  # Default: do not wipe
```

**Documentation comment:**
```yaml
# Set to true to remove application completely
# Wipe only:    ansible-playbook deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
# Clean install: ansible-playbook deploy.yml -e "web_app_wipe=true"
```

#### 3.5 Testing Wipe Logic

**Test Scenarios:**

**Scenario 1: Normal deployment (wipe should NOT run)**
```bash
ansible-playbook playbooks/deploy.yml

# Verify: app deploys normally, wipe tasks skipped (tag not specified)
ssh user@vm_ip "docker ps"
```

**Scenario 2: Wipe only (remove existing deployment)**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Verify: app should be removed, deployment skipped
ssh user@vm_ip "docker ps"  # Should not show app
ssh user@vm_ip "ls /opt"    # Should not have app directory
```

**Scenario 3: Clean reinstallation (wipe → deploy)**
```bash
# This is the KEY use case: fresh start
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"

# What happens:
# 1. Wipe tasks run first (remove old installation)
# 2. Deployment tasks run second (install fresh)
# Result: clean reinstallation

# Verify: old app removed, new app running
ssh user@vm_ip "docker ps"
```

**Scenario 4: Safety checks (should NOT wipe)**
```bash
# 4a: Tag specified but variable false (when condition blocks it)
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# Result: wipe tasks skipped, deployment runs normally

# 4b: Variable true, deployment skipped (only wipe runs)
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
# Result: only wipe, no deployment
```

**Evidence Required:**
- Output of Scenario 1 showing normal deployment (wipe skipped)
- Output of Scenario 2 showing wipe-only operation
- Output of Scenario 3 showing clean reinstall (wipe → deploy)
- Output of Scenario 4a showing wipe blocked by when condition
- Screenshot of application running after clean reinstall

#### 3.6 Research Questions

Answer these in your documentation:
1. **Why use both variable AND tag?** (Double safety mechanism)
2. **What's the difference between `never` tag and this approach?**
3. **Why must wipe logic come BEFORE deployment in main.yml?** (Clean reinstall scenario)
4. **When would you want clean reinstallation vs. rolling update?**
5. **How would you extend this to wipe Docker images and volumes too?**

---

### Task 4 — CI/CD with GitHub Actions (3 pts)

#### 4.1 Why Automate Ansible?

**Benefits:**
- **Consistency** - same process every time
- **Speed** - automatic deployments on push
- **Safety** - linting catches errors before execution
- **Auditability** - GitHub logs every deployment
- **Integration** - combines with testing, building, scanning

**CI/CD Flow:**
```
Code Push → Lint Ansible → Run Ansible Playbook → Verify Deployment
```

#### 4.2 Install GitHub Actions Runner (Optional)

**Two Approaches:**

**Approach A: Self-hosted runner on target VM (Recommended)**
- More realistic for production
- Direct access to target server
- Faster (no SSH overhead)
- Setup: GitHub Repo → Settings → Actions → Runners → Add runner

**Approach B: GitHub-hosted runner with SSH**
- Easier setup
- Requires SSH key configuration
- Uses GitHub Secrets for credentials
- Slower but simpler

Choose based on your infrastructure preference.

#### 4.3 Create Ansible Workflow

**File:** `.github/workflows/ansible-deploy.yml`

**Requirements:**
1. Trigger on push to ansible directory
2. Run ansible-lint for syntax checking
3. Execute Ansible playbook
4. Verify deployment success
5. Use path filters to avoid unnecessary runs

**Workflow Structure:**
```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'ansible/**'

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
        run: |
          pip install ansible ansible-lint

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest  # or self-hosted
    steps:
      # Add deployment steps
      # - Setup Ansible
      # - Configure SSH (if needed)
      # - Decrypt Vault (use GitHub Secrets)
      # - Run playbook
      # - Verify deployment
```

#### 4.4 Configure GitHub Secrets

**Required Secrets:** (Settings → Secrets and variables → Actions)

1. `ANSIBLE_VAULT_PASSWORD` - Vault password for decryption
2. `SSH_PRIVATE_KEY` - SSH key for target VM (if using remote runner)
3. `VM_HOST` - Target VM IP/hostname
4. `VM_USER` - SSH username

**Using Secrets in Workflow:**
```yaml
- name: Deploy with Ansible
  env:
    ANSIBLE_VAULT_PASSWORD: ${{ secrets.ANSIBLE_VAULT_PASSWORD }}
  run: |
    echo "$ANSIBLE_VAULT_PASSWORD" > /tmp/vault_pass
    ansible-playbook playbooks/deploy.yml \
      --vault-password-file /tmp/vault_pass
    rm /tmp/vault_pass
```

#### 4.5 Implement Deployment Step

**For self-hosted runner:**
```yaml
deploy:
  runs-on: self-hosted
  steps:
    - uses: actions/checkout@v4

    - name: Deploy with Ansible
      run: |
        cd ansible
        echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
        ansible-playbook playbooks/deploy.yml \
          --vault-password-file /tmp/vault_pass \
          --tags "app_deploy"
        rm /tmp/vault_pass
```

**For GitHub-hosted runner:**
```yaml
deploy:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

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
      run: |
        cd ansible
        echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
        ansible-playbook playbooks/deploy.yml \
          -i inventory/hosts.ini \
          --vault-password-file /tmp/vault_pass
        rm /tmp/vault_pass
```

#### 4.6 Add Verification Step

**After deployment, verify it worked:**
```yaml
- name: Verify Deployment
  run: |
    sleep 10  # Wait for app to start
    curl -f http://${{ secrets.VM_HOST }}:8000 || exit 1
    curl -f http://${{ secrets.VM_HOST }}:8000/health || exit 1
```

#### 4.7 Path Filters Best Practice

**Why path filters?**
- Don't run Ansible workflow when changing docs
- Separate workflows for different concerns
- Faster CI, lower costs

**Example:**
```yaml
on:
  push:
    paths:
      - 'ansible/**'           # Ansible code
      - '!ansible/docs/**'     # Exclude docs
      - '.github/workflows/ansible-deploy.yml'  # Workflow changes
```

#### 4.8 Add Status Badge

**File:** `README.md` (or ansible/README.md)

**Add badge:**
```markdown
[![Ansible Deployment](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml)
```

#### 4.9 Testing CI/CD

**Test Sequence:**
1. Make a change to ansible code (e.g., update variable in group_vars)
2. Commit and push to GitHub
3. Watch Actions tab for workflow execution
4. Verify lint job passes
5. Verify deploy job succeeds
6. Check application is updated on target VM

**Evidence Required:**
- Screenshot of successful workflow run
- Output logs showing ansible-lint passing
- Output logs showing ansible-playbook execution
- Verification step output showing app responding
- Status badge in README showing passing

#### 4.10 Research Questions

Answer in documentation:
1. **What are the security implications of storing SSH keys in GitHub Secrets?**
2. **How would you implement a staging → production deployment pipeline?**
3. **What would you add to make rollbacks possible?**
4. **How does self-hosted runner improve security compared to GitHub-hosted?**

---

### Task 5 — Documentation (1 pt)

Create `ansible/docs/LAB06.md` with the following:

**Required Sections:**
1. **Overview** - What you accomplished and technologies used
2. **Blocks & Tags** - Block usage in each role, tag strategy, execution examples with screenshots
3. **Docker Compose Migration** - Template structure, role dependencies, before/after comparison
4. **Wipe Logic** - Implementation details, variable + tag approach, test results
5. **CI/CD Integration** - Workflow architecture, setup steps, evidence of automated deployments
6. **Testing Results** - All test scenarios, idempotency verification, application accessibility
7. **Challenges & Solutions** - Difficulties encountered and how you solved them
8. **Research Answers** - All research questions answered with analysis

**Code Documentation:**
- Add clear comments in all modified Ansible files
- Document variables in templates
- Explain safety mechanisms in wipe logic
- Document workflow steps in CI/CD files

**Evidence:**
- Terminal outputs showing tagged execution
- Wipe logic test results (all 4 scenarios)
- CI/CD workflow logs and screenshots
- Application accessibility verification

---

### Bonus Part 1 — Multi-App Deployment (1.5 pts)

#### Bonus 1.1 Prerequisites

**Required:**
- Completed Lab 1 Bonus (compiled language app: Go/Rust/Java/C#)
- Completed Lab 2 Bonus (multi-stage Docker build)
- Completed Lab 3 Bonus Part 1 (multi-app CI/CD)

**You should have:**
- Python web app (everyone has this)
- Compiled language web app (Go/Rust/Java/C#)
- Both apps containerized and on Docker Hub
- Both apps with similar endpoints (/, /health)

#### Bonus 1.2 Role Reusability Pattern

**Key Concept:** Use the same `web_app` role for both apps with different variables.

**Directory Structure:**
```
ansible/
├── inventory/
│   └── hosts.ini
├── group_vars/
│   └── all.yml
├── host_vars/          # Optional: per-host vars
├── vars/
│   ├── app_python.yml  # NEW: Python app variables
│   └── app_bonus.yml   # NEW: Bonus app variables
├── roles/
│   └── web_app/        # Reused for both apps
└── playbooks/
    ├── provision.yml
    ├── deploy_python.yml    # NEW
    ├── deploy_bonus.yml     # NEW
    └── deploy_all.yml       # NEW: Deploy both
```

#### Bonus 1.3 Create Variable Files

**File:** `ansible/vars/app_python.yml`
```yaml
---
app_name: devops-python
docker_image: your_username/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000
compose_project_dir: "/opt/{{ app_name }}"
```

**File:** `ansible/vars/app_bonus.yml`
```yaml
---
app_name: devops-go  # or rust, java, csharp
docker_image: your_username/devops-info-service-go
docker_tag: latest
app_port: 8001  # Different port!
app_internal_port: 8080  # Go apps often use 8080
compose_project_dir: "/opt/{{ app_name }}"
```

**Important:** Use different ports to run both apps simultaneously.

#### Bonus 1.4 Create Deployment Playbooks

**File:** `ansible/playbooks/deploy_python.yml`
```yaml
---
- name: Deploy Python Application
  hosts: all
  become: true
  vars_files:
    - ../vars/app_python.yml

  roles:
    - web_app
```

**File:** `ansible/playbooks/deploy_bonus.yml`
```yaml
---
- name: Deploy Bonus Application
  hosts: all
  become: true
  vars_files:
    - ../vars/app_bonus.yml

  roles:
    - web_app
```

**File:** `ansible/playbooks/deploy_all.yml`
```yaml
---
- name: Deploy All Applications
  hosts: all
  become: true

  tasks:
    - name: Deploy Python App
      include_role:
        name: web_app
      vars:
        app_name: devops-python
        docker_image: your_username/devops-info-service
        app_port: 8000

    - name: Deploy Bonus App
      include_role:
        name: web_app
      vars:
        app_name: devops-go
        docker_image: your_username/devops-info-service-go
        app_port: 8001
        app_internal_port: 8080
```

#### Bonus 1.5 Extend Wipe Logic

**Wipe logic should support app-specific wipe:**

**Usage:**
```bash
# Wipe only Python app
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Wipe only Bonus app
ansible-playbook playbooks/deploy_bonus.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

# Wipe both apps
ansible-playbook playbooks/deploy_all.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```

**The role automatically handles different apps because `app_name` and `compose_project_dir` are different!**

#### Bonus 1.6 Testing Multi-App Deployment

**Test Commands:**
```bash
# Deploy both apps
ansible-playbook playbooks/deploy_all.yml

# Verify both running
ssh user@vm_ip "docker ps"
curl http://vm_ip:8000        # Python app
curl http://vm_ip:8001        # Bonus app

# Test independent deployment
ansible-playbook playbooks/deploy_python.yml  # Should not affect bonus app
ansible-playbook playbooks/deploy_bonus.yml   # Should not affect python app

# Test independent wipe
ansible-playbook playbooks/deploy_python.yml \
  -e "web_app_wipe=true" --tags web_app_wipe
# Verify: Python app removed, bonus app still running

# Test idempotency
ansible-playbook playbooks/deploy_all.yml
ansible-playbook playbooks/deploy_all.yml  # Should show minimal changes
```

**Evidence Required:**
- Output showing both apps deployed
- `docker ps` output showing both containers
- Curl outputs from both apps
- Proof of independent wipe functionality
- Idempotency verification for multi-app deployment

#### Bonus 1.7 Documentation

**Add to LAB06.md:**
- Multi-app architecture explanation
- Variable file strategy
- Role reusability benefits
- Port conflict resolution
- Independent vs. combined deployment trade-offs

---

### Bonus Part 2 — Multi-App CI/CD (1 pt)

#### Bonus 2.1 Prerequisites

**Required:**
- Bonus Part 1 completed (multi-app deployment working)
- Task 4 completed (single app CI/CD working)

#### Bonus 2.2 Workflow Strategy

**Two Approaches:**

**Approach A: Separate Workflows**
- One workflow per app
- Path filters for each app's code
- Independent deployment
- More control, more files

**Approach B: Matrix Strategy**
- Single workflow with matrix
- Deploys both apps
- Simpler, less flexible

Choose based on your preference (Approach A recommended).

#### Bonus 2.3 Create Workflow for Bonus App

**File:** `.github/workflows/ansible-deploy-bonus.yml`

**Requirements:**
1. Trigger on bonus app code changes
2. Run ansible-lint
3. Deploy bonus app only
4. Verify bonus app responds
5. Independent from Python app workflow

**Path Filters:**
```yaml
on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/vars/app_bonus.yml'
      - 'ansible/playbooks/deploy_bonus.yml'
      - 'ansible/roles/web_app/**'
      - '.github/workflows/ansible-deploy-bonus.yml'
```

**Deployment Step:**
```yaml
- name: Deploy Bonus Application
  run: |
    cd ansible
    echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
    ansible-playbook playbooks/deploy_bonus.yml \
      --vault-password-file /tmp/vault_pass
    rm /tmp/vault_pass
```

**Verification:**
```yaml
- name: Verify Bonus App Deployment
  run: |
    sleep 10
    curl -f http://${{ secrets.VM_HOST }}:8001 || exit 1
    curl -f http://${{ secrets.VM_HOST }}:8001/health || exit 1
```

#### Bonus 2.4 Update Python App Workflow

**File:** `.github/workflows/ansible-deploy.yml`

**Update path filters to be more specific:**
```yaml
on:
  push:
    paths:
      - 'ansible/vars/app_python.yml'
      - 'ansible/playbooks/deploy_python.yml'
      - 'ansible/playbooks/deploy.yml'  # If this deploys Python
      - 'ansible/roles/web_app/**'
      - '.github/workflows/ansible-deploy.yml'
```

**Update deployment to use specific playbook:**
```yaml
- name: Deploy Python Application
  run: |
    cd ansible
    ansible-playbook playbooks/deploy_python.yml \
      --vault-password-file /tmp/vault_pass
```

#### Bonus 2.5 Matrix Strategy Alternative

**File:** `.github/workflows/ansible-deploy-matrix.yml`

**Using matrix to deploy both:**
```yaml
name: Ansible Multi-App Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app:
          - name: python
            playbook: deploy_python.yml
            port: 8000
          - name: bonus
            playbook: deploy_bonus.yml
            port: 8001

    steps:
      - uses: actions/checkout@v4

      - name: Deploy ${{ matrix.app.name }}
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/${{ matrix.app.playbook }} \
            --vault-password-file /tmp/vault_pass
          rm /tmp/vault_pass

      - name: Verify ${{ matrix.app.name }}
        run: |
          sleep 10
          curl -f http://${{ secrets.VM_HOST }}:${{ matrix.app.port }}
```

#### Bonus 2.6 Testing Multi-App CI/CD

**Test Scenarios:**

**Test 1: Python app change should deploy only Python**
```bash
# Change ansible/vars/app_python.yml
git add ansible/vars/app_python.yml
git commit -m "Update Python app config"
git push

# Watch Actions - only ansible-deploy.yml should run
# Verify only Python app redeployed
```

**Test 2: Bonus app change should deploy only Bonus**
```bash
# Change ansible/vars/app_bonus.yml
git add ansible/vars/app_bonus.yml
git commit -m "Update Bonus app config"
git push

# Watch Actions - only ansible-deploy-bonus.yml should run
```

**Test 3: Role change should deploy both**
```bash
# Change ansible/roles/web_app/tasks/main.yml
git add ansible/roles/web_app/
git commit -m "Update web_app role"
git push

# Watch Actions - both workflows should run
```

**Evidence Required:**
- Screenshots showing independent workflow triggers
- Logs proving only affected app deployed
- Verification of both apps working after role change
- Status badges for both workflows

#### Bonus 2.7 Documentation

**Add to LAB06.md:**
- Multi-app CI/CD architecture
- Workflow triggering logic
- Path filter strategy
- Matrix vs separate workflows comparison
- Evidence of independent deployments

---

## Submission Guidelines

### What to Submit

Submit a single markdown file: **`ansible/docs/LAB06.md`**

### Required Structure

```markdown
# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Your Name
**Date:** YYYY-MM-DD
**Lab Points:** 10 + X bonus

---

## Task 1: Blocks & Tags (2 pts)
[Your implementation details]
[Evidence: terminal outputs, tag listings]
[Research answers]

## Task 2: Docker Compose (3 pts)
[Your implementation]
[Template code]
[Before/after comparison]
[Evidence: deployments, idempotency]

## Task 3: Wipe Logic (1 pt)
[Implementation explanation]
[Test results for all scenarios]
[Evidence proving correct behavior]

## Task 4: CI/CD (3 pts)
[Workflow setup]
[Secrets configuration]
[Evidence: successful runs, badges]

## Task 5: Documentation
[This file serves as documentation]

## Bonus Part 1: Multi-App (1.5 pts)
[If completed]

## Bonus Part 2: Multi-App CI/CD (1 pt)
[If completed]

---

## Summary
[Overall reflection]
[Total time spent]
[Key learnings]
```

### GitHub Repository Requirements

**Commit all code:**
```bash
git add ansible/
git add .github/workflows/
git add ansible/docs/LAB06.md
git commit -m "Complete Lab 6: Advanced Ansible & CI/CD"
git push
```

**Repository should contain:**
- ✅ Updated roles with blocks and tags
- ✅ Docker Compose templates
- ✅ Wipe logic implementation
- ✅ CI/CD workflows
- ✅ Documentation with evidence
- ✅ Working deployments (apps accessible)

### Evidence Checklist

**Required Proof:**
- [ ] Ansible playbook output with selective tags
- [ ] Rescue block triggered output
- [ ] Docker Compose deployment success
- [ ] Idempotency verification (2nd run)
- [ ] Wipe logic test results (all 4 scenarios)
- [ ] GitHub Actions successful workflow
- [ ] ansible-lint passing
- [ ] Status badge(s) in README
- [ ] Application(s) accessible via curl

**Bonus Proof (if applicable):**
- [ ] Both apps deployed and accessible
- [ ] Independent wipe functionality
- [ ] Separate workflow runs for each app
- [ ] Path filter effectiveness demonstrated

---

## Checklist

**Before submitting, ensure you have:**
- [ ] All three roles refactored with blocks and tags
- [ ] Docker Compose deployment working with templated config
- [ ] Role dependencies correctly configured
- [ ] Wipe logic implemented with variable + tag safety
- [ ] All 4 wipe scenarios tested successfully
- [ ] GitHub Actions workflow running and passing
- [ ] ansible-lint integrated and passing
- [ ] Path filters configured for efficient CI/CD
- [ ] Complete documentation in `ansible/docs/LAB06.md`
- [ ] All research questions answered
- [ ] Terminal outputs and screenshots included
- [ ] Application(s) accessible and verified

**Bonus (if attempting):**
- [ ] Second app deployed using role reusability
- [ ] Independent wipe logic for each app
- [ ] Separate CI/CD workflows or matrix strategy
- [ ] Path filters for independent triggering

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Blocks & Tags** | 2 pts | All roles refactored with blocks, rescue/always, comprehensive tag strategy |
| **Docker Compose** | 3 pts | Working templated deployment, role dependencies, idempotent |
| **Wipe Logic** | 1 pt | Variable + tag implementation, all scenarios tested |
| **CI/CD** | 3 pts | Automated workflow with linting, deployment, verification |
| **Documentation** | 1 pt | Complete LAB06.md with evidence and analysis |
| **Bonus: Multi-App** | 1.5 pts | Role reusability, independent deployment and wipe |
| **Bonus: Multi-App CI/CD** | 1 pt | Separate workflows or matrix, independent triggering |
| **Total** | 12.5 pts | 10 pts required + 2.5 pts bonus |

**Grading Scale:**
- **10/10:** All tasks working, excellent documentation, proper implementation
- **8-9/10:** All works, good docs, minor improvements possible
- **6-7/10:** Core functionality present, basic documentation
- **<6/10:** Missing features or documentation, needs revision

---

## Resources

<details>
<summary>📚 Ansible Documentation</summary>

- [Ansible Blocks](https://docs.ansible.com/ansible/latest/user_guide/playbooks_blocks.html)
- [Ansible Tags](https://docs.ansible.com/ansible/latest/user_guide/playbooks_tags.html)
- [Ansible Role Dependencies](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html#using-role-dependencies)
- [Ansible Variables](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html)
- [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)

</details>

<details>
<summary>🐳 Docker Compose</summary>

- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Compose Module](https://docs.ansible.com/ansible/latest/collections/community/docker/docker_compose_module.html)
- [community.docker Collection](https://docs.ansible.com/ansible/latest/collections/community/docker/)
- [Compose Best Practices](https://docs.docker.com/compose/production/)

</details>

<details>
<summary>🔄 CI/CD & GitHub Actions</summary>

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions: Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Self-hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

</details>

<details>
<summary>🛠️ Tools & Best Practices</summary>

- [ansible-lint](https://ansible-lint.readthedocs.io/) - Best practices checker
- [Ansible Galaxy](https://galaxy.ansible.com/) - Community roles
- [Jinja2 Templating](https://jinja.palletsprojects.com/) - Template engine
- [YAML Syntax](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html)

</details>

---

## Looking Ahead

Your Ansible automation evolves throughout the course:

- **Lab 7:** Logging Stack - Deploy Loki, Promtail, and Grafana
- **Lab 8:** Metrics Stack - Add Prometheus metrics to your app
- **Lab 9:** Kubernetes Basics - Migrate from Docker Compose to K8s deployments
- **Lab 10:** Helm charts for templated K8s deployments
- **Lab 11-12:** Secrets with Vault, ConfigMaps, and persistent storage
- **Lab 13:** GitOps with ArgoCD - Declarative Kubernetes deployments

---

**Good luck!** 🚀
