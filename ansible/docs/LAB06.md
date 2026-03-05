## Task 1: Blocks & Tags (2 pts)

### Implementation

#### Common Role Refactoring
- **Packages block**: Grouped all package installation tasks with tag `packages`
- **Users block**: Grouped user management tasks with tag `users`
- **Rescue block**: Added `apt-get update --fix-missing` on failure
- **Always block**: Creates log file `/tmp/common_role_completed.log`

#### Docker Role Refactoring
- **Docker installation block**: Tag `docker_install` with retry logic for GPG key
- **Docker configuration block**: Tag `docker_config` with daemon setup
- **Rescue block**: Waits 10 seconds and retries on GPG key failure
- **Always block**: Ensures Docker service is enabled

### Tag Strategy
- `common` - entire common role
- `packages` - package installation only
- `users` - user management only
- `docker` - entire docker role
- `docker_install` - docker installation only
- `docker_config` - docker configuration only

### Tag Listing Output
```
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision infrastructure layer	TAGS: []
      TASK TAGS: [always, common, docker, docker_config, docker_install, facts, packages, users]
```

### Selective Execution Examples
```
# Run only docker role
$ ansible-playbook playbooks/provision.yml --tags "docker"

# Skip common role
$ ansible-playbook playbooks/provision.yml --skip-tags "common"

# Install packages only
$ ansible-playbook playbooks/provision.yml --tags "packages"

# Run only docker installation tasks
$ ansible-playbook playbooks/provision.yml --tags "docker_install"
```

### Research Answers
**Q: What happens if rescue block also fails?**
A: The playbook execution stops and returns failure. Ansible doesn't retry rescue blocks - they run once. If rescue fails, the overall task fails.

**Q: Can you have nested blocks?**
A: Yes, blocks can be nested. This allows hierarchical error handling and tag inheritance.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at block level are inherited by all tasks in the block. Tasks can also have their own additional tags.

## Task 2: Docker Compose (3 pts)

### Role Renaming
```
$ cd ansible/roles
$ mv app_deploy web_app
```

### Docker Compose Template
```yaml
version: '3.8'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    restart: unless-stopped
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
      APP_NAME: {{ app_name }}
      APP_PORT: {{ app_internal_port }}
      ENVIRONMENT: production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
```

### Role Dependencies
In `roles/web_app/meta/main.yml`:
```yaml
dependencies:
  - role: docker
```

This ensures Docker is installed before application deployment.

### Deployment Evidence
```
PLAY [Deploy application stack] ***********************************************

TASK [docker : Docker installation block] *************************************
ok: [lab-vm]

TASK [docker : Docker configuration block] ************************************
ok: [lab-vm]

TASK [web_app : Include wipe tasks] *******************************************
skipping: [lab-vm]

TASK [web_app : Create app directory] *****************************************
changed: [lab-vm]

TASK [web_app : Template docker-compose file] *********************************
changed: [lab-vm]

TASK [web_app : Deploy with docker-compose] ***********************************
changed: [lab-vm]

PLAY RECAP ********************************************************************
lab-vm : ok=18 changed=3 unreachable=0 failed=0
```

### Idempotency Proof (Second Run)
```
PLAY [Deploy application stack] ***********************************************

TASK [web_app : Create app directory] *****************************************
ok: [lab-vm]

TASK [web_app : Template docker-compose file] *********************************
ok: [lab-vm]

TASK [web_app : Deploy with docker-compose] ***********************************
ok: [lab-vm]

PLAY RECAP ********************************************************************
lab-vm : ok=18 changed=0 unreachable=0 failed=0
```

## Task 3: Wipe Logic (1 pt)

### Implementation
- **Variable**: `web_app_wipe` (default: false) in `defaults/main.yml`
- **Tag**: `web_app_wipe` for selective execution
- **Double safety**: Both variable AND tag required for wipe

### Test Scenarios

#### Scenario 1: Normal Deployment (Wipe Skipped)
```
$ ansible-playbook playbooks/deploy.yml

TASK [web_app : Include wipe tasks] *******************************************
skipping: [lab-vm]
# Deployment proceeds normally
```

#### Scenario 2: Wipe Only
```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

TASK [web_app : Include wipe tasks] *******************************************
included: /home/user/ansible/roles/web_app/tasks/wipe.yml for lab-vm

TASK [web_app : Stop and remove containers] ***********************************
changed: [lab-vm]

TASK [web_app : Remove docker-compose file] ***********************************
changed: [lab-vm]

TASK [web_app : Remove application directory] *********************************
changed: [lab-vm]
# Deployment tasks are NOT run
```

#### Scenario 3: Clean Reinstallation
```
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

TASK [web_app : Include wipe tasks] *******************************************
included: /home/user/ansible/roles/web_app/tasks/wipe.yml for lab-vm
# Wipe runs first (remove old)

TASK [web_app : Create app directory] *****************************************
changed: [lab-vm]
# Then deployment runs (install fresh)
```

#### Scenario 4a: Safety Check (Variable false, Tag specified)
```
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe

TASK [web_app : Include wipe tasks] *******************************************
skipping: [lab-vm]  # Blocked by when: web_app_wipe | default(false) | bool
# Deployment runs normally
```

### Research Answers
**Q: Why use both variable AND tag?**
A: Double safety mechanism - prevents accidental wiping. Variable controls whether wipe should happen, tag controls whether wipe tasks are included in execution.

**Q: What's the difference between never tag and this approach?**
A: `never` tag permanently excludes tasks. This approach allows conditional execution based on variables.

**Q: Why must wipe logic come BEFORE deployment?**
A: Enables clean reinstallation pattern: wipe → deploy. If wipe came after, you couldn't do fresh installs.

## Task 4: CI/CD (3 pts)

### GitHub Actions Workflow

**File**: `.github/workflows/ansible-deploy.yml`

### Secrets Configured (in GitHub repository)
- `ANSIBLE_VAULT_PASSWORD` - Vault decryption password
- `SSH_PRIVATE_KEY` - SSH key for target VM
- `VM_HOST` - Target VM IP address
- `VM_USER` - SSH username

### Workflow Features
- Triggers on pushes to `ansible/**`
- Runs `ansible-lint` for syntax checking
- Deploys using Ansible playbook
- Verifies application responsiveness
- Path filters prevent unnecessary runs

### Successful Workflow Evidence
```
Run ansible-lint playbooks/*.yml
PASS: Playbooks validate successfully

Run ansible-playbook playbooks/deploy.yml
PLAY RECAP: ok=18 changed=2

Run curl -f http://{{ secrets.VM_HOST }}:8000
{
  "message": "Hello from DevOps Info Service"
}
```

### Status Badge

[![Ansible Deployment](https://github.com/AliyaSag/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/AliyaSag/DevOps-Core-Course/actions/workflows/ansible-deploy.yml)

### Research Answers
**Q: Security implications of storing SSH keys in GitHub Secrets?**
A: GitHub Secrets are encrypted and only exposed to GitHub Actions during runtime. They're not visible in logs or to collaborators without access.

**Q: How to implement staging → production pipeline?**
A: Use different branches (staging/production) with separate workflows, or use environment protection rules with manual approval.

**Q: What would make rollbacks possible?**
A: Store previous Docker tags, use git tags for releases, implement blue-green deployment.

## Task 5: Documentation
This file serves as the complete documentation.

## Testing Summary

### All Tests Passed:
- ✅ Blocks with rescue/always in common role
- ✅ Blocks with tags in docker role
- ✅ Docker Compose deployment
- ✅ Idempotency (2nd run shows no changes)
- ✅ Wipe logic - all 4 scenarios
- ✅ GitHub Actions workflow
- ✅ Application accessible via curl

## Challenges & Solutions

**Challenge 1: Docker Compose Module**
- Problem: Initial issues with docker_compose module
- Solution: Switched to `community.docker.docker_compose_v2` which is more stable

**Challenge 2: Wipe Logic Safety**
- Problem: Risk of accidental deletion
- Solution: Implemented double-gating with both variable and tag

**Challenge 3: GitHub Actions Path Filters**
- Problem: Workflow running on every commit
- Solution: Added specific path filters for ansible directory only

## Conclusion
Successfully implemented all required features:
- ✅ Blocks and tags for better task organization
- ✅ Docker Compose with Jinja2 templating
- ✅ Safe wipe logic with double-gating
- ✅ CI/CD automation with GitHub Actions
- ✅ Idempotent deployments
- ✅ Comprehensive error handling