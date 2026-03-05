# Lab 6: Advanced Ansible & CI/CD - Solution

Complete Ansible automation with blocks, tags, Docker Compose, role dependencies, wipe logic, and CI/CD integration.

## Structure

```
lab06-solution/
├── ansible/
│   ├── playbooks/
│   │   ├── provision.yml      # Common + Docker installation
│   │   └── deploy.yml         # Web app deployment
│   ├── roles/
│   │   ├── common/            # OS packages with blocks/tags
│   │   ├── docker/            # Docker installation with error handling
│   │   └── web_app/           # Docker Compose deployment (renamed from app_deploy)
│   ├── inventory/
│   │   └── hosts.ini
│   ├── group_vars/
│   │   └── all.yml
│   ├── ansible.cfg
│   ├── requirements.yml
│   └── README.md
├── .github/
│   └── workflows/
│       └── ansible-deploy.yml # CI/CD pipeline
└── README.md
```

## Tasks Implemented

**Task 1: Blocks & Tags (2 pts)**
- Common role: package installation blocks with rescue/always
- Docker role: installation & configuration blocks with retry logic
- Comprehensive tag strategy for selective execution

**Task 2: Docker Compose (3 pts)**
- Renamed `app_deploy` → `web_app` role
- Jinja2 templating for docker-compose.yml
- Role dependencies for Docker installation  
- Idempotent deployments

**Task 3: Wipe Logic (1 pt)**
- Variable + tag double-gating (not "never" tag)
- Safe application removal
- Clean reinstallation support

**Task 4: CI/CD (3 pts)**
- GitHub Actions workflow with lint and validate jobs
- ansible-lint integration
- Playbook syntax validation

## Execution

```bash
# Provision infrastructure
ansible-playbook playbooks/provision.yml --tags docker

# Deploy application
ansible-playbook playbooks/deploy.yml

# Clean reinstall (wipe → deploy)
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

# List available tags
ansible-playbook playbooks/provision.yml --list-tags
```

## Key Features

- **Error Handling**: Rescue blocks with retry logic for network issues
- **Idempotency**: Safe to run multiple times
- **Security**: Variable + tag gating for destructive operations
- **CI/CD Ready**: GitHub Actions integration with linting
- **Role Reusability**: web_app role can deploy different apps with variables
