# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** ellilin
**Date:** 2026-03-05
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation Details

#### 1.1 Common Role Refactoring

**File:** `roles/common/tasks/main.yml`

**Key Features:**
- **Package Installation Block**: Groups all package-related tasks with rescue logic
- **System Configuration Block**: Manages user and timezone settings
- Rescue blocks handle failures gracefully
- Always blocks log completion

**Tag Strategy:**
- `packages` - Package installation tasks
- `users` - User management tasks
- `common` - Entire role

#### 1.2 Docker Role Refactoring

**File:** `roles/docker/tasks/main.yml`

**Key Features:**
- **Docker Installation Block**: Installs Docker with retry logic for GPG key failures
- **Docker Configuration Block**: Configures Docker user and dependencies
- Rescue block handles GPG key timeouts
- Always block ensures Docker is running

**Tag Strategy:**
- `docker` - Entire role
- `docker_install` - Installation tasks only
- `docker_config` - Configuration tasks only

### Testing Results

**List all available tags:**
```bash
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, provision, users]
```

**Run with specific tags:**
```bash
$ ansible-playbook playbooks/provision.yml --tags "docker_install"
# Result: Only Docker installation tasks ran, configuration skipped

$ ansible-playbook playbooks/provision.yml --skip-tags "common"
# Result: Common role skipped, only Docker ran
```

### Research Answers

**Q: What happens if rescue block also fails?**
A: If the rescue block fails, the entire play will fail for that host. Ansible will move to the next host or stop execution. You can use `ignore_errors: yes` or add multiple rescue tasks to prevent complete failure.

**Q: Can you have nested blocks?**
A: Yes, Ansible supports nested blocks. However, it's generally better to keep them simple for readability.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at the block level are inherited by all tasks within that block. You can also apply tags to individual tasks for more granular control.

---

## Task 2: Docker Compose Migration (3 pts)

### Implementation Details

**Renamed** `app_deploy` to `web_app` for better semantic clarity.

**File:** `roles/web_app/templates/docker-compose.yml.j2`

Docker Compose template with Jinja2:
- Dynamic service name, image, ports
- Environment variable support
- Restart policy configuration
- Health check support
- Labels for organization

### Role Dependencies

**File:** `roles/web_app/meta/main.yml`

The `web_app` role depends on the `docker` role, ensuring Docker is installed before deploying applications.

### Testing Results

**Test 1: Initial Deployment**
```bash
$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY RECAP *********************************************************************
3.238.44.67                : ok=23   changed=9    unreachable=0    failed=0    skipped=6    rescued=1    ignored=1
```

**Test 2: Idempotency Check**
```bash
$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY RECAP *********************************************************************
3.238.44.67                : ok=23   changed=1    unreachable=0    failed=0    skipped=6    rescued=0    ignored=1
```
Result: Second run shows minimal changes (idempotent behavior confirmed)

**Test 3: Verify Application**
```bash
$ curl -s http://3.238.44.67:5000/health
{"status":"healthy","timestamp":"2026-03-05T18:27:12.226182+00:00","uptime_seconds":427}

$ docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
NAMES                STATUS                    PORTS
devops-info-python   Up 7 minutes (healthy)    0.0.0.0:5000->5000/tcp
```

### Before/After Comparison

**Before (docker run):**
- Manual container management
- Hard to configure multi-container setups

**After (Docker Compose):**
- Declarative configuration
- Easy multi-container management
- Simple cleanup with `docker compose down`
- Reproducible deployments

---

## Task 3: Wipe Logic Implementation (1 pt)

### Implementation Details

**File:** `roles/web_app/tasks/wipe.yml`

**Safety Mechanisms:**
- **Variable Gate**: `web_app_wipe` variable (default: false)
- **Tag Gate**: `web_app_wipe` tag
- **Double-Gating**: Both variable AND tag must be specified for wipe to run

### Test Scenarios

**Scenario 1: Normal Deployment (wipe should NOT run)**
```bash
$ ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
# Result: Wipe tasks skipped (web_app_wipe defaults to false)
```

**Scenario 2: Wipe Only**
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass

TASK [web_app : Stop and remove containers] ***
changed: [3.238.44.67]
TASK [web_app : Remove docker-compose file] ***
changed: [3.238.44.67]
TASK [web_app : Remove application directory] ***
changed: [3.238.44.67]

PLAY RECAP *********************************************************************
3.238.44.67                : ok=7    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

**Scenario 3: Clean Reinstallation**
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass
# Result: Wipe runs first, then deployment runs (wipe → deploy)
```

**Scenario 4: Tag Without Variable**
```bash
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe --vault-password-file .vault_pass
# Result: Wipe tasks skipped (variable gate prevents execution)
```

### Research Answers

**Q: Why use both variable AND tag?**
A: This provides double safety. The variable prevents accidental wipes during normal playbook reviews, while the tag ensures wipe tasks only run when explicitly requested.

**Q: Why must wipe logic come BEFORE deployment in main.yml?**
A: Wipe must come first to enable clean reinstallation. When both wipe and deploy run, the order is: wipe removes old → deploy creates fresh installation.

**Q: When would you want clean reinstallation vs. rolling update?**
A: Clean reinstallation for major version upgrades, configuration changes that can't be applied in-place, security incidents. Rolling updates for minor version updates, zero-downtime requirements.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

**Workflow Structure:**
1. **Lint Job**: Runs on GitHub-hosted runner
   - Installs Ansible and ansible-lint
   - Validates all playbooks and role tasks

2. **Deploy Job**: Runs on self-hosted runner
   - Depends on successful lint job
   - Only runs on push to main/master branches
   - Deploys application using Ansible
   - Verifies deployment success

### GitHub Secrets Configuration

Required secret:
- `ANSIBLE_VAULT_PASSWORD` - Password for decrypting Ansible Vault

### Self-Hosted Runner Setup

Runner installed on AWS VM:
```bash
# Create folder
mkdir actions-runner && cd actions-runner

# Download runner
curl -o actions-runner-linux-x64-2.332.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.332.0/actions-runner-linux-x64-2.332.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.332.0.tar.gz

# Configure
./config.sh --url https://github.com/ellilin/DevOps --token ASHR6JCHDTHEXH356DR3C4LJVHSRG

# Install and start service
sudo ./svc.sh install
sudo ./svc.sh start
```

Runner Status:
```
● actions.runner.ellilin-DevOps.ip-10-0-1-237.service - GitHub Actions Runner
     Loaded: loaded; enabled; vendor preset: enabled
     Active: active (running)
```

### Status Badge

Added to README.md:
```markdown
[![Ansible Deployment](https://github.com/ellilin/DevOps/workflows/Ansible%20Deployment/badge.svg)](https://github.com/ellilin/DevOps/actions/workflows/ansible-deploy.yml)
```
<img width="901" height="312" alt="image" src="https://github.com/user-attachments/assets/17029cf3-d65e-444d-b815-2c5545eec8be" />
<img width="658" height="327" alt="image" src="https://github.com/user-attachments/assets/1add0a25-a31d-465b-9c51-f6396b81fee8" />


---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

**Variable Files:**
- `ansible/vars/app_python.yml` - Python app on port 5000
- `ansible/vars/app_bonus.yml` - Go app on port 5001

**Playbooks:**
- `ansible/playbooks/deploy_python.yml`
- `ansible/playbooks/deploy_bonus.yml`
- `ansible/playbooks/deploy_all.yml`

### Testing Results

**Deploy both apps:**
```bash
$ ansible-playbook playbooks/deploy_all.yml --vault-password-file .vault_pass

PLAY RECAP *********************************************************************
3.238.44.67                : ok=32   changed=3    unreachable=0    failed=0    skipped=13   rescued=1    ignored=1
```

**Verify both apps running:**
```bash
$ curl -s http://3.238.44.67:5000/health
{"status":"healthy","timestamp":"2026-03-05T18:27:12.226182+00:00","uptime_seconds":427}

$ curl -s http://3.238.44.67:5001/health
{"status":"healthy","timestamp":"2026-03-05T18:27:12Z","uptime_seconds":39}

$ docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
NAMES                STATUS                    PORTS
devops-go            Up 41 seconds (healthy)   0.0.0.0:5001->8080/tcp
devops-info-python   Up 7 minutes (healthy)    0.0.0.0:5000->5000/tcp
```

### Independent Wipe

```bash
# Wipe only Python app
$ ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe
# Result: Python app removed, Go app still running
```

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Workflow Architecture

Created separate workflows:
- `.github/workflows/ansible-deploy.yml` - Main deployment
- `.github/workflows/ansible-deploy-python.yml` - Python app only
- `.github/workflows/ansible-deploy-bonus.yml` - Go app only

### Path Filter Strategy

Each workflow has specific path filters:
- Python: triggers on `ansible/vars/app_python.yml` changes
- Go: triggers on `ansible/vars/app_bonus.yml` changes
- Both: trigger on `ansible/roles/web_app/**` changes

### Status Badges

```markdown
[![Ansible Deployment](https://github.com/ellilin/DevOps/workflows/Ansible%20Deployment/badge.svg)](https://github.com/ellilin/DevOps/actions/workflows/ansible-deploy.yml)
[![Python App](https://github.com/ellilin/DevOps/workflows/Ansible%20Python%20App%20Deployment/badge.svg)](https://github.com/ellilin/DevOps/actions/workflows/ansible-deploy-python.yml)
[![Go App](https://github.com/ellilin/DevOps/workflows/Ansible%20Bonus%20App%20Deployment/badge.svg)](https://github.com/ellilin/DevOps/actions/workflows/ansible-deploy-bonus.yml)
```

---

## Challenges & Solutions

### Challenge 1: Docker Compose Module Compatibility
**Problem:** The `community.docker.docker_compose_v2` module requires the docker-compose Python library, which has compatibility issues with Python 3.12 and Ubuntu 24.04's PEP 668 restrictions.

**Solution:** Switched to using `docker compose` CLI commands directly via the `command` module. This works with the native `docker-compose-plugin` installed via apt.

### Challenge 2: Wipe Logic Execution Order
**Problem:** Initially unclear whether wipe should come before or after deployment tasks.

**Solution:** Placed wipe tasks at the beginning of `main.yml` to enable clean reinstallation workflow (wipe → deploy). This allows users to run `ansible-playbook deploy.yml -e "web_app_wipe=true"` for a fresh start.

### Challenge 3: Multi-App Port Conflicts
**Problem:** Running both Python and Go apps simultaneously would cause port conflicts.

**Solution:** Configured different ports for each application:
- Python app: port 5000 (internal: 5000)
- Go app: port 5001 (internal: 8080)

### Challenge 4: GitHub Actions Self-Hosted Runner
**Problem:** Workflows require a runner with access to the target VM.

**Solution:** Installed and configured a self-hosted runner on the EC2 instance, configured as a systemd service for automatic startup.

### Challenge 5: Ansible Vault in CI/CD
**Problem:** Encrypted variables need to be decrypted during automated deployments.

**Solution:** Stored the vault password in GitHub Secrets and wrote it to a temp file during the workflow run, then cleaned it up after deployment.

---

## Summary

### Accomplishments

| Task | Points | Status |
|------|--------|--------|
| Blocks & Tags | 2 pts | ✅ Complete |
| Docker Compose | 3 pts | ✅ Complete |
| Wipe Logic | 1 pt | ✅ Complete |
| CI/CD | 3 pts | ✅ Complete |
| Documentation | 1 pt | ✅ Complete |
| Bonus: Multi-App | 1.5 pts | ✅ Complete |
| Bonus: Multi-App CI/CD | 1 pt | ✅ Complete |
| **Total** | **12.5 pts** | ✅ |

### Infrastructure

**AWS Resources Created:**
- VPC: vpc-05aabbb2e8020911d
- Subnet: subnet-0e15a9cd4b289dd37
- Security Group: sg-034d0e566ed6b8fbe
- EC2 Instance: i-0e6579cb79c71740e (3.238.44.67)

**Open Ports:**
- 22 (SSH)
- 80 (HTTP)
- 5000 (Python app)
- 5001 (Go app)

### Working URLs

- **Python App**: http://3.238.44.67:5000
- **Go App**: http://3.238.44.67:5001
- **Health Checks**:
  - http://3.238.44.67:5000/health
  - http://3.238.44.67:5001/health

---

## Files Modified

- `ansible/roles/common/tasks/main.yml` - Blocks and tags
- `ansible/roles/docker/tasks/main.yml` - Blocks and tags
- `ansible/roles/web_app/` - Docker Compose, wipe logic
- `ansible/vars/app_python.yml` - Python app variables
- `ansible/vars/app_bonus.yml` - Go app variables
- `ansible/playbooks/deploy_python.yml`
- `ansible/playbooks/deploy_bonus.yml`
- `ansible/playbooks/deploy_all.yml`
- `.github/workflows/ansible-deploy.yml`
- `.github/workflows/ansible-deploy-python.yml`
- `.github/workflows/ansible-deploy-bonus.yml`
- `terraform/main.tf` - Updated for Lab 6
- `terraform/variables.tf` - Updated prefix
