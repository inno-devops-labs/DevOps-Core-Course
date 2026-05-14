# Lab 06 — Advanced Ansible & CI/CD


---

## Task 1: Blocks & Tags (2 pts)

### Block usage in roles

Both `common` and `docker` roles refactored with block/rescue/always structure.

**common role** — one block with tags `packages`, `common`:
- block: update apt cache + install packages
- rescue: fix-missing retry on apt failure
- always: debug log completion

**docker role** — two blocks:
- Install block (tags: `docker`, `docker_install`): GPG key, repo, packages
- Config block (tags: `docker`, `docker_config`): service, user, python3-docker
- rescue: wait 10s and retry GPG key on network failure
- always: ensure Docker service enabled

### Tag strategy

| Tag | What runs |
|-----|-----------|
| `common` | entire common role |
| `packages` | package installation only |
| `docker` | entire docker role |
| `docker_install` | Docker installation only |
| `docker_config` | Docker configuration only |
| `app_deploy` | application deployment |
| `compose` | Docker Compose tasks |
| `web_app_wipe` | wipe logic only |

### Available tags output:
playbook: playbooks/provision.yml
play #1 (webservers): Provision web servers   TAGS: []
TASK TAGS: [common, docker, docker_config, docker_install, packages]

### Selective execution with --tags "docker":
TASK [docker : Install required system packages] ok
TASK [docker : Create directory for Docker GPG key] ok
TASK [docker : Add Docker GPG key] ok
TASK [docker : Add Docker repository] ok
TASK [docker : Install Docker packages] ok
TASK [docker : Ensure Docker service is running and enabled] ok
TASK [docker : Add user to docker group] ok
TASK [docker : Install python3-docker] ok
TASK [docker : Ensure Docker service is enabled] ok
PLAY RECAP: ok=10  changed=0  unreachable=0  failed=0

Common role skipped entirely — only docker tasks ran.

---

## Task 2: Docker Compose Migration (3 pts)

### Role renamed: app_deploy → web_app

### Template: roles/web_app/templates/docker-compose.yml.j2
```yaml
services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_image_tag }}
    container_name: {{ app_container_name }}
    ports:
      - "{{ app_port }}:{{ app_port }}"
    restart: {{ app_restart_policy }}
    environment:
      - APP_ENV=production
```

### Role dependency (meta/main.yml):
```yaml
dependencies:
  - role: docker
```

Docker role runs automatically before web_app.

### Before (Lab 5): docker run via shell
```bash
docker run -d --name devops-app --restart unless-stopped -p 5000:5000 image:tag
```

### After (Lab 6): Docker Compose
```bash
docker compose -f /opt/devops-app/docker-compose.yml up -d --remove-orphans
```

### First deployment output:
TASK [web_app : Create application directory] changed
TASK [web_app : Template docker-compose file] changed
TASK [web_app : Login to Docker Hub] changed
TASK [web_app : Pull latest Docker image] changed
TASK [web_app : Deploy with Docker Compose] changed
TASK [web_app : Wait for application to be ready] ok
TASK [web_app : Verify application health] ok
TASK [web_app : Show health check result] ok: "App is running, status: 200"
PLAY RECAP: ok=19  changed=4  failed=0

### Second deployment (idempotency):
TASK [web_app : Create application directory] ok
TASK [web_app : Template docker-compose file] ok
TASK [web_app : Login to Docker Hub] changed
TASK [web_app : Pull latest Docker image] changed
TASK [web_app : Deploy with Docker Compose] changed
PLAY RECAP: ok=19  changed=3  failed=0

Directory and template are idempotent (ok). Docker login/pull/compose use shell module so always show changed — expected behavior for shell commands.

### Templated docker-compose.yml rendered on VM:
```yaml
services:
  lab02-python-app:
    image: nadiaa02/lab02-python-app:latest
    container_name: devops-app
    ports:
      - "5000:5000"
    restart: unless-stopped
    environment:
      - APP_ENV=production
```

### Application verification:
curl http://93.77.181.6:5000/
{"service":{"name":"devops-info-service","version":"1.0.0"},...}
HTTP Status: 200 OK

---

## Task 3: Wipe Logic (1 pt)

### Implementation

**roles/web_app/defaults/main.yml:**
```yaml
web_app_wipe: false  # Default: do not wipe
```

**roles/web_app/tasks/wipe.yml:**
- Double gate: when: web_app_wipe | bool + tag web_app_wipe
- Runs docker compose down then removes directory
- Uses ignore_errors: yes for already-clean state

### Why both variable AND tag?
Variable alone could accidentally wipe if wrong vars passed. Tag alone could accidentally wipe if someone runs all tags. Both together require explicit intent — must set variable AND specify tag simultaneously.

### What is the difference between never tag and this approach?
The never tag permanently prevents a task from running unless explicitly called — it is a hard block built into Ansible. Our approach uses a when condition which is dynamic and can be overridden per-run with -e flag. More flexible for CI/CD pipelines.

### Why must wipe logic come BEFORE deployment?
To support clean reinstallation. Flow: remove old state then install new. If reversed, you would deploy fresh and immediately wipe it.

### Test Results

**Scenario 1 — Normal deployment (wipe skipped):**
```bash
ansible-playbook playbooks/deploy.yml
```
TASK [web_app : Stop and remove containers] skipping
TASK [web_app : Remove application directory] skipping
TASK [web_app : Log wipe completion] skipping
PLAY RECAP: changed=4  failed=0
Result: Wipe tasks skipped, app deployed normally.

**Scenario 2 — Wipe only:**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```
TASK [web_app : Stop and remove containers] changed
TASK [web_app : Remove application directory] changed
TASK [web_app : Log wipe completion] ok: "Application lab02-python-app wiped successfully"
PLAY RECAP: ok=5  changed=2  failed=0
Result: Only wipe ran, deployment skipped entirely.

**Scenario 3 — Clean reinstall (wipe then deploy):**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```
TASK [web_app : Stop and remove containers] changed (ignored error - already clean)
TASK [web_app : Remove application directory] ok
TASK [web_app : Log wipe completion] ok
TASK [web_app : Create application directory] changed
TASK [web_app : Deploy with Docker Compose] changed
TASK [web_app : Show health check result] ok: "App is running, status: 200"
PLAY RECAP: ok=22  changed=6  ignored=1
Result: Old app removed, new app deployed fresh and verified.

**Scenario 4 — Safety check (tag set but variable false):**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```
TASK [web_app : Stop and remove containers] skipping
TASK [web_app : Remove application directory] skipping
TASK [web_app : Log wipe completion] skipping
PLAY RECAP: ok=2  changed=0  skipped=3
Result: when: web_app_wipe | bool blocked execution because variable was false.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow file: .github/workflows/ansible-deploy.yml

**Triggers:**
- Push to master branch with changes in ansible/ directory
- Pull request to master with changes in ansible/ directory
- Excludes ansible/docs/ changes (no deploy needed for docs)

**Jobs:**

**lint job:**
- Installs ansible and ansible-lint
- Runs ansible-lint on provision.yml and deploy.yml
- Must pass before deploy job runs

**deploy job (needs: lint):**
- Sets up Python 3.12 and Ansible
- Configures SSH using SSH_PRIVATE_KEY secret
- Creates vault password file from ANSIBLE_VAULT_PASSWORD secret
- Updates inventory with VM_HOST and VM_USER from secrets
- Runs ansible-playbook deploy.yml
- Cleans up vault password file
- Verifies deployment with curl to port 5000

**GitHub Secrets configured:**
- ANSIBLE_VAULT_PASSWORD — vault password for decryption
- SSH_PRIVATE_KEY — private key for VM access
- VM_HOST — target VM IP address (93.77.181.6)
- VM_USER — SSH username (ubuntu)

**Path filters:**
```yaml
paths:
  - 'ansible/**'
  - '!ansible/docs/**'
  - '.github/workflows/ansible-deploy.yml'
```
Only runs when Ansible code changes, not on docs updates.

---

## Key Decisions

**Why use roles instead of plain playbooks?**
Roles enforce separation of concerns and make code reusable. The docker role can be used in any project. Plain playbooks become monolithic and hard to maintain as complexity grows.

**What makes a task idempotent?**
A task is idempotent when it checks current state before acting and only makes changes when needed. Ansible modules like apt, service, file, template do this automatically. Shell commands do not.

**How do handlers improve efficiency?**
Handlers only run once at end of play even if notified multiple times. Docker restart handler will not fire repeatedly if multiple tasks notify it.

**When would you want clean reinstallation vs rolling update?**
Clean reinstall for major version changes, corrupted state, or config structure changes. Rolling update for minor patches with zero-downtime requirement.

**How would you extend wipe to include Docker images and volumes?**
Add tasks: docker rmi for the image and docker volume rm for named volumes. Add a prune_images boolean variable defaulting to false to make it optional.

**Security implications of storing SSH keys in GitHub Secrets?**
Secrets are encrypted at rest and only exposed to workflow runs on the correct branch. Risk exists if repository is compromised or if secrets are accidentally printed in logs. Mitigate with no_log and careful output handling.

**How would you implement staging to production pipeline?**
Add two environments in GitHub Actions (staging, production). Deploy to staging first, run integration tests, then require manual approval before deploying to production using environment protection rules.

**What would you add for rollbacks?**
Tag Docker images with git commit SHA instead of latest. Keep previous image tag in Ansible variable. On failure in rescue block, redeploy previous tag automatically.
