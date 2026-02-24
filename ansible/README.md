# Ansible Lab 05: Infrastructure Provisioning & Deployment

## Quick Start

### 1. Activate Virtual Environment
```bash
cd /home/j0cos/innopolis/Devops/DevOps-Core-Course
source .venv/bin/activate
cd ansible
```

### 2. Configure the environment variable and load them into context
```bash
set -a                                 
source .env
set +a
```

### 3. Run Complete Deployment
```bash
ansible-playbook playbooks/site.yml -v
```

### 4. Test Application Health
```bash
curl http://[ip_adress]:5000/health
```

---

## Project Structure

```
ansible/
├── ansible.cfg                    # Ansible configuration
├── inventory/
│   └── hosts.ini                 # VM inventory (46.21.244.46)
├── roles/
│   ├── common/                   # System provisioning
│   │   ├── defaults/main.yml    # Packages, timezone
│   │   └── tasks/main.yml       # APT updates, installs
│   ├── docker/                   # Container engine
│   │   ├── defaults/main.yml    # Docker packages
│   │   ├── handlers/main.yml    # Service restart logic
│   │   └── tasks/main.yml       # Install, enable, login
│   └── app_deploy/               # Application deployment
│       ├── defaults/main.yml    # Container config
│       └── tasks/main.yml       # Pull image, deploy, health
├── playbooks/
│   ├── site.yml                 # Full provisioning + deploy
│   ├── provision.yml            # System + Docker only
│   └── health_check.yml         # Health endpoint tests
├── group_vars/
│   └── webservers.yml          # Host group variables
└── test_application.sh          # Health check testing
└── .env                        #  env. vars
```

---

## Available Playbooks

### 1. Full Deployment (Recommended)
```bash
ansible-playbook playbooks/site.yml -v
```
Executes: common role → docker role → app_deploy role

### 2. System Provisioning Only
```bash
ansible-playbook playbooks/provision.yml
```
Executes: common role → docker role (no application)

### 3. Health Check
```bash
ansible-playbook playbooks/health_check.yml
```
Tests: /health endpoint on deployed application

---

## Idempotency Demonstration

Run the playbook twice to see idempotency in action:

```bash
# First run - will make changes
ansible-playbook playbooks/site.yml -v

# Second run - no changes (all tasks return "ok")
ansible-playbook playbooks/site.yml -v
```

**Expected Second Run Output:**
```
TASK [common : Update apt cache]
ok: [lab4-vm] => {"changed": false}

TASK [common : Install common packages]
ok: [lab4-vm] => {"changed": false}

TASK [docker : Install Docker packages]
ok: [lab4-vm] => {"changed": false}

PLAY RECAP
lab4-vm : ok=16 changed=0 unreachable=0 failed=0
```

---

## Deployed Application

**URL:** http://46.21.244.46:5000

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Service info (system, uptime, request details) |
| `/health` | GET | Health check for monitoring |

### Quick Test
```bash
# Health check
curl http://46.21.244.46:5000/health

# Full service info
curl http://46.21.244.46:5000/ | python3 -m json.tool
```

---

## Roles Explained

### Common Role
Handles system-level provisioning:
- Updates APT package cache
- Upgrades all packages
- Installs development tools (gcc, make, pip, etc.)
- Sets system timezone (UTC)
- Configures system resource limits

### Docker Role
Manages container engine:
- Installs docker.io and docker-compose
- Enables and starts Docker service
- Adds ubuntu user to docker group
- Authenticates with Docker Hub (j0cos)
- Provides handlers for service restarts

### App Deploy Role
Orchestrates application deployment:
- Pulls Docker image (j0cos/devops-info-service:latest)
- Removes any existing container
- Deploys new container with health checks
- Validates application readiness via /health endpoint
- Sets restart policy to "always"

---

## Docker Hub Credentials

```
Username: j0cos
Password: qwerty123 (stored in group_vars)
```

Ansible uses these to pull and push Docker images.

---

## VM Details

**Infrastructure:** Yandex Cloud (Terraform-provisioned)
- **Image:** Ubuntu 24.04 LTS
- **IP:** 46.21.244.46
- **Cores:** 2 (20% guaranteed)
- **Memory:** 1 GB
- **Disk:** 10 GB

---

## Configuration Files

### ansible.cfg
```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
remote_user = ubuntu

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```

### inventory/hosts.ini
```ini
[webservers]
lab4-vm ansible_host=46.21.244.46 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

---

## Troubleshooting

### SSH Connection Issues
```bash
# Test connectivity
ansible webservers -m ping

# Check SSH key permissions
ls -la ~/.ssh/id_ed25519
```

### Docker Issues
```bash
# Check Docker service status (on VM)
systemctl status docker

# View container logs
docker logs devops-info-service
```

### Playbook Debugging
```bash
# Run with extra verbosity
ansible-playbook playbooks/site.yml -vvv

# Run specific task
ansible-playbook playbooks/site.yml --tags docker
```

---

## Key Learnings

1. **Idempotency:** Ansible playbooks are idempotent - run them multiple times safely
2. **Roles:** Organize tasks into reusable, modular components
3. **Handlers:** Trigger actions based on task changes (e.g., service restarts)
4. **Health Checks:** Docker native health monitoring with curl endpoints
5. **Security:** Non-root containers, credential management, least privilege
6. **Infrastructure as Code:** Reproducible deployments with Terraform + Ansible

---

## Files Summary

✅ **Configuration Files**
- `ansible.cfg` - Ansible configuration
- `inventory/hosts.ini` - Host inventory

✅ **Roles**
- `roles/common/` - System provisioning
- `roles/docker/` - Container engine setup
- `roles/app_deploy/` - Application deployment

✅ **Playbooks**
- `playbooks/site.yml` - Complete deployment
- `playbooks/provision.yml` - System + Docker only
- `playbooks/health_check.yml` - Health endpoint tests

✅ **Utilities**
- `run_idempotency_test.sh` - Demonstrates idempotency
- `test_application.sh` - Tests application endpoints

✅ **Documentation**
- `README.md` - This file
- `LAB05.md` - Complete lab documentation

---

## Next Steps

1. **Monitor Application:** Check health endpoint regularly
2. **Scale Deployment:** Add more VMs to inventory
3. **Implement CI/CD:** Automate playbook runs on push
4. **Add Vault:** Encrypt sensitive credentials
5. **Enable Monitoring:** Add Prometheus/Grafana metrics

---

**Lab 05 Complete! 🚀**

For full documentation, see `LAB05.md`
