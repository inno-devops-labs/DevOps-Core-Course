# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Ko Zimin
**Date:** 2026-03-05
**Lab Points:** 10 + 0 bonus

---

## Configuration Requirements

Before running the Ansible playbooks, you need to configure the following:

### 1. Ansible Vault Variables

The `ansible/group_vars/all.yml` file is encrypted with Ansible Vault and should contain your Docker Hub credentials:

```yaml
# Docker Hub Credentials (from GitHub Repository Secrets)
dockerhub_username: plaffyyy9
dockerhub_password: "{{ vault_dockerhub_password }}"

# Application Configuration
app_name: devops-app
docker_image: plaffyyy9/devops-info-service
docker_tag: latest
app_port: 8000
app_internal_port: 8000
```

To edit the vault file:
```bash
cd ansible
ansible-vault edit group_vars/all.yml
```

The `vault_dockerhub_password` should be encrypted with Ansible Vault and can be set from the `DOCKER_PASSWORD` GitHub secret.

### 2. GitHub Actions Secrets

For CI/CD to work, the following secrets should already be configured in your GitHub repository:
- `DOCKER_PASSWORD` and `DOCKER_USERNAME` for Docker Hub authentication
- `SSH_PRIVATE_KEY`: Private SSH key for VM access
- `VM_HOST`: IP address of your target VM (93.77.188.243)
- `ANSIBLE_VAULT_PASSWORD`: Password to decrypt the vault file

The `VM_HOST` secret should contain your VM's IP address (89.169.150.5). Even though this is currently hardcoded in the inventory file, using a GitHub secret makes the workflow more flexible for different environments.

### 3. Dependencies Installation

Install required dependencies:
```bash
# Install Ansible collections
ansible-galaxy collection install community.docker

# Install Python dependencies
pip3 install docker
```

---

## Task 1: Blocks & Tags (2 pts)

### Implementation Details

I've refactored both the `common` and `docker` roles to use blocks and tags for better organization and selective execution.

### Common Role Refactoring

In `ansible/roles/common/tasks/main.yml`, I've organized tasks into logical blocks:
- **Package management block** with tag `packages` that handles apt cache updates and package installations
- **User management block** with tag `users` for user-related tasks
- Added error handling with rescue blocks for apt cache failures
- Added always blocks to log completion of each section
- Applied `become: true` at the block level instead of per task

### Docker Role Refactoring

In `ansible/roles/docker/tasks/main.yml`, I've organized tasks into:
- **Docker installation block** with tag `docker_install` that handles package installation
- **Docker configuration block** with tag `docker_config` that handles service configuration
- Added rescue block to handle Docker GPG key failures with retry logic
- Added always block to ensure Docker service is enabled

### Tag Strategy

Tags implemented:
- `packages` - all package installation tasks
- `users` - all user management tasks
- `common` - entire common role
- `docker` - entire docker role
- `docker_install` - Docker installation only
- `docker_config` - Docker configuration only

### Research Answers

**Q: What happens if rescue block also fails?**
If a rescue block also fails, Ansible will stop executing the play and report the failure. The tasks in the rescue block are treated like regular tasks, and if they fail, the play fails.

**Q: Can you have nested blocks?**
Yes, Ansible supports nested blocks. You can have blocks within blocks to create more granular error handling and task grouping.

**Q: How do tags inherit to tasks within blocks?**
Tags applied to a block are inherited by all tasks within that block. If a task has its own tags, those are merged with the block's tags.

---

## Task 2: Docker Compose (3 pts)

### Implementation Details

I've upgraded the deployment method from individual `docker run` commands to Docker Compose for better application management.

### Role Renaming

Renamed the `app_deploy` role to `web_app` to better reflect its purpose and prepare for potential multi-app deployments:
```bash
cd ansible/roles
mv app_deploy web_app
```

### Docker Compose Template

Created `ansible/roles/web_app/templates/docker-compose.yml.j2` with Jinja2 templating:
- Dynamic service name, image, and port configuration
- Support for environment variables
- Restart policy configuration
- Version management

### Role Dependencies

Added `ansible/roles/web_app/meta/main.yml` to define role dependencies:
- The `web_app` role now automatically requires the `docker` role to be executed first
- This ensures Docker is installed before attempting to deploy applications

### Docker Compose Deployment

Updated `ansible/roles/web_app/tasks/main.yml` to:
- Create application directory
- Template the docker-compose.yml file
- Deploy using the `community.docker.docker_compose_v2` module
- Include error handling with rescue blocks

### Research Answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
- `restart: always` will always restart the container if it stops, regardless of the reason
- `restart: unless-stopped` will restart the container unless it was explicitly stopped by the user

**Q: How do Docker Compose networks differ from Docker bridge networks?**
Docker Compose automatically creates a default network for services in the same compose file, allowing them to communicate using service names. Bridge networks are manually created and require explicit connection of containers.

**Q: Can you reference Ansible Vault variables in the template?**
Yes, Ansible Vault variables can be referenced in templates just like regular variables. They are decrypted automatically during playbook execution.

---

## Task 3: Wipe Logic (1 pt)

### Implementation Details

Implemented safe wipe logic with double-gating mechanism (variable + tag) to prevent accidental deletions.

### Wipe Tasks

Created `ansible/roles/web_app/tasks/wipe.yml` with:
- Container removal using Docker Compose
- Removal of docker-compose.yml file
- Removal of application directory
- Logging of wipe completion

### Main Tasks Integration

Updated `ansible/roles/web_app/tasks/main.yml` to include wipe tasks at the beginning:
- Wipe logic runs first when explicitly requested
- Enables clean reinstallation: wipe → deploy workflow

### Wipe Variable Configuration

Added `web_app_wipe: false` to `ansible/roles/web_app/defaults/main.yml`:
- Controls whether wipe tasks should run
- Default behavior is to not wipe (safe by default)
- Well-documented with usage examples

### Research Answers

**1. Why use both variable AND tag?**
Using both provides a double safety mechanism. The variable acts as a configuration flag, while the tag provides explicit invocation control. Both must be satisfied for wipe tasks to run, preventing accidental deletions.

**2. What's the difference between `never` tag and this approach?**
The `never` tag completely excludes tasks unless explicitly included. Our approach allows tasks to be included by default but controlled by a variable, providing more flexibility.

**3. Why must wipe logic come BEFORE deployment in main.yml?**
This enables the clean reinstall scenario where wipe tasks run first to remove old installations, followed by deployment tasks to install fresh versions.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstallation is preferred when making significant configuration changes, troubleshooting issues, or ensuring a pristine environment. Rolling updates are better for minor updates with minimal downtime.

**5. How would you extend this to wipe Docker images and volumes too?**
Add additional tasks to the wipe.yml file to remove Docker images with `docker_image` module and volumes with `docker_volume` module, with appropriate conditions and error handling.

---

## Task 4: CI/CD (3 pts)

### Workflow Architecture

Created `.github/workflows/ansible-deploy.yml` with a two-job workflow:
1. **Lint Job**: Runs ansible-lint for syntax checking
2. **Deploy Job**: Executes Ansible playbook and verifies deployment

### Setup Steps

The workflow includes:
- Path filtering to only run on Ansible-related changes
- Python setup and Ansible installation
- SSH key configuration for remote deployment
- Ansible Vault password handling via GitHub Secrets
- Deployment verification with curl commands

### Evidence of Automated Deployments

The workflow automatically triggers on pushes to the main/master branch when Ansible files are modified, runs linting, deploys the application, and verifies it's working correctly.

### Research Answers

**1. What are the security implications of storing SSH keys in GitHub Secrets?**
Storing SSH keys in GitHub Secrets is secure as they are encrypted at rest and only decrypted during workflow execution. However, the private key should have minimal privileges and be rotated regularly.

**2. How would you implement a staging → production deployment pipeline?**
Create separate workflows or use GitHub Environments with different inventories and variables for staging and production environments, with manual approvals for production deployments.

**3. What would you add to make rollbacks possible?**
Implement versioned deployments, store previous configurations, and create rollback playbooks that can revert to previous versions.

**4. How does self-hosted runner improve security compared to GitHub-hosted?**
Self-hosted runners don't require exposing SSH keys in GitHub Secrets and can run in a more controlled network environment with direct access to target systems.

---

## Task 5: Documentation

This file serves as the complete documentation for Lab 6 implementation.

---

## Summary

In this lab, I enhanced the Ansible automation with advanced features including blocks for error handling, tags for selective execution, Docker Compose for better application management, safe wipe logic with double-gating, and CI/CD integration with GitHub Actions.

**Total time spent:** Approximately 8 hours
**Key learnings:**
- Blocks and tags significantly improve Ansible playbook organization and execution flexibility
- Docker Compose provides better application lifecycle management than individual docker commands
- Double-gating mechanisms are essential for safe destructive operations
- CI/CD automation reduces human error and speeds up deployment processes
- Proper documentation is crucial for maintaining complex automation systems
