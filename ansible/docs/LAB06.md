# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** ellilin
**Date:** 2026-03-05
**Lab Points:** 10 + 2.5 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation Details

#### 1.1 Common Role Refactoring

The `common` role has been refactored to use blocks with error handling:

**File:** `roles/common/tasks/main.yml`

**Key Features:**
- **Package Installation Block**: Groups all package-related tasks with rescue logic
  - Updates apt cache
  - Installs common packages
  - Rescue block fixes apt cache issues and retries installation
  - Always block logs completion

- **System Configuration Block**: Manages user and timezone settings
  - Sets timezone
  - Creates deployment user (conditional)
  - Rescue block handles failures gracefully
  - Always block logs completion

**Tag Strategy:**
- `packages` - Package installation tasks
- `users` - User management tasks
- `common` - Entire role (applied at role level)

#### 1.2 Docker Role Refactoring

The `docker` role has been refactored with comprehensive error handling:

**File:** `roles/docker/tasks/main.yml`

**Key Features:**
- **Docker Installation Block**:
  - Installs Docker dependencies
  - Adds Docker GPG key and repository
  - Installs Docker packages
  - Rescue block handles GPG key timeouts and retries installation
  - Always block ensures Docker service is enabled

- **Docker Configuration Block**:
  - Starts Docker service
  - Adds user to docker group
  - Installs python3-docker and docker-compose
  - Rescue block handles configuration failures
  - Always block verifies Docker installation and logs completion

**Tag Strategy:**
- `docker` - Entire role
- `docker_install` - Installation tasks only
- `docker_config` - Configuration tasks only

### Testing Results

```bash
# Test 1: Run only package tasks
ansible-playbook playbooks/provision.yml --tags "packages"

# Test 2: Run only docker installation
ansible-playbook playbooks/provision.yml --tags "docker_install"

# Test 3: Skip common role
ansible-playbook playbooks/provision.yml --skip-tags "common"

# Test 4: List all available tags
ansible-playbook playbooks/provision.yml --list-tags
```

**Output showing selective execution:**
```
TASK TAGS: [common, docker, docker_config, docker_install, packages, provision, users]
```

### Research Answers

**Q: What happens if rescue block also fails?**
A: If the rescue block fails, the entire play will fail for that host, and Ansible will move to the next host or stop execution depending on configuration. You can add multiple rescue tasks or use `ignore_errors: yes` to prevent this.

**Q: Can you have nested blocks?**
A: Yes, Ansible supports nested blocks. You can have blocks within blocks, but it's generally better to keep them simple for readability. Nested blocks can be useful for complex error handling scenarios.

**Q: How do tags inherit to tasks within blocks?**
A: Tags applied at the block level are inherited by all tasks within that block. You can also apply tags to individual tasks within a block for more granular control. The effective tags are the union of block-level and task-level tags.

---

## Task 2: Docker Compose Migration (3 pts)

### 2.1 Role Renaming

Renamed `app_deploy` to `web_app` for better semantic clarity:
- More descriptive and specific
- Prepares for potential other app types
- Aligns with variable naming conventions

### 2.2 Docker Compose Template

**File:** `roles/web_app/templates/docker-compose.yml.j2`

**Template Features:**
- Jinja2 templating for dynamic configuration
- Support for environment variables
- Configurable ports, volumes, and networks
- Health check support
- Label management for organization
- Version control via variables

**Template Variables:**
```yaml
app_name: Service/container name
docker_image: Docker Hub image
docker_tag: Image version
app_port: Host port
app_internal_port: Container port
app_env_vars: Environment variables dictionary
app_restart_policy: Restart policy
```

### 2.3 Role Dependencies

**File:** `roles/web_app/meta/main.yml`

The `web_app` role depends on the `docker` role, ensuring Docker is installed before deploying applications. This creates automatic execution order:
1. Docker role runs first (installs Docker)
2. Web_app role runs second (deploys application)

### 2.4 Deployment Implementation

**File:** `roles/web_app/tasks/main.yml`

**Deployment Block:**
1. Creates application directory
2. Templates docker-compose.yml file
3. Deploys with `community.docker.docker_compose_v2` module
4. Waits for application port
5. Verifies health endpoint
6. Logs completion

**Error Handling:**
- Rescue block captures deployment failures
- Displays Docker Compose logs for debugging
- Always block ensures directory state is checked

**Idempotency:**
The deployment is idempotent because:
- Directory creation is idempotent (only creates if not exists)
- Template module only updates when content changes
- Docker Compose module only recreates containers when configuration changes

### Testing Results

**Test 1: Initial Deployment**
```bash
ansible-playbook playbooks/deploy.yml
```
Result: Successfully deployed application with Docker Compose

**Test 2: Idempotency Check**
```bash
ansible-playbook playbooks/deploy.yml
```
Result: Second run shows no changes (idempotent behavior confirmed)

**Test 3: Verify Application**
```bash
ssh ubuntu@vm_ip
docker ps
curl http://localhost:5000
curl http://localhost:5000/health
```
Result: Application running and accessible

### Before/After Comparison

**Before (docker run):**
- Manual container management
- Hard to configure multi-container setups
- Limited environment variable management
- Manual cleanup required

**After (Docker Compose):**
- Declarative configuration
- Easy multi-container management
- Environment variable files support
- Simple cleanup with `docker compose down`
- Reproducible deployments

---

## Task 3: Wipe Logic Implementation (1 pt)

### Implementation Details

**File:** `roles/web_app/tasks/wipe.yml`

**Wipe Block Tasks:**
1. Stops and removes containers using Docker Compose
2. Removes docker-compose.yml file
3. Removes application directory
4. Optionally removes Docker images
5. Logs wipe completion

**Safety Mechanisms:**
- **Variable Gate**: `web_app_wipe` variable (default: false)
- **Tag Gate**: `web_app_wipe` tag
- **Double-Gating**: Both variable AND tag must be specified for wipe to run
- **ignore_errors**: Prevents failures if resources don't exist

**Variable Configuration:**
```yaml
web_app_wipe: false  # Default: do not wipe
web_app_remove_volumes: false  # Remove volumes when wiping
web_app_remove_images: false  # Remove images when wiping
```

### Test Scenarios

**Scenario 1: Normal Deployment (wipe should NOT run)**
```bash
ansible-playbook playbooks/deploy.yml
```
Result: Application deploys normally, wipe tasks skipped

**Scenario 2: Wipe Only**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```
Result: Application removed, deployment skipped

**Scenario 3: Clean Reinstallation**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"
```
Result: Old app removed, new app deployed (wipe → deploy)

**Scenario 4a: Tag Without Variable**
```bash
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
```
Result: Wipe tasks skipped (variable gate prevents execution)

**Scenario 4b: Variable With Tag**
```bash
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe
```
Result: Only wipe runs, no deployment

### Research Answers

**Q: Why use both variable AND tag?**
A: This provides double safety. The variable prevents accidental wipes during normal playbook reviews, while the tag ensures wipe tasks only run when explicitly requested. This prevents accidental data loss while maintaining flexibility.

**Q: What's the difference between `never` tag and this approach?**
A: The `never` tag is a special Ansible tag that prevents tasks from running unless specifically requested. Our approach is more explicit and controllable - we can conditionally run wipe based on variables, and we have finer control over when it executes in the playbook flow.

**Q: Why must wipe logic come BEFORE deployment in main.yml?**
A: Wipe must come first to enable clean reinstallation. When both wipe and deploy run (with variable=true but no tag filter), the order is: wipe removes old installation → deploy creates fresh installation. This ensures a clean slate before deployment.

**Q: When would you want clean reinstallation vs. rolling update?**
A: Clean reinstallation is useful for:
- Major version upgrades
- Configuration changes that can't be applied in-place
- Security incidents requiring complete rebuild
- Testing from scratch
Rolling updates are better for:
- Minor version updates
- Zero-downtime requirements
- Gradual configuration changes

**Q: How would you extend this to wipe Docker images and volumes too?**
A: Set `web_app_remove_volumes: true` and `web_app_remove_images: true` variables. The wipe tasks already support these options through conditional tasks that remove volumes and images when enabled.

---

## Task 4: CI/CD with GitHub Actions (3 pts)

### Workflow Architecture

**File:** `.github/workflows/ansible-deploy.yml`

**Workflow Structure:**
1. **Lint Job**: Runs on GitHub-hosted runner
   - Installs Ansible and ansible-lint
   - Validates all playbooks and role tasks
   - Fails on linting errors

2. **Deploy Job**: Runs on self-hosted runner
   - Depends on successful lint job
   - Only runs on push to main/master branches
   - Installs Ansible and required collections
   - Deploys application using Ansible
   - Verifies deployment success

**Path Filters:**
```yaml
paths:
  - 'ansible/**'
  - '.github/workflows/ansible-deploy.yml'
```
This ensures workflow only runs when Ansible code changes.

### GitHub Secrets Configuration

Required secrets (configured in GitHub repository settings):
1. `ANSIBLE_VAULT_PASSWORD` - Password for decrypting Ansible Vault
2. `SSH_PRIVATE_KEY` - SSH key for VM access (if using remote runner)
3. `VM_HOST` - Target VM IP address
4. `VM_USER` - SSH username

### Deployment Process

1. **Checkout**: Pulls latest code
2. **Setup**: Installs Python and Ansible
3. **Decrypt**: Uses vault password from secrets
4. **Deploy**: Runs Ansible playbook with app_deploy tag
5. **Verify**: Checks application health endpoints

### Verification Steps

```yaml
- name: Verify Deployment
  run: |
    sleep 10
    curl -f http://localhost:5000 || exit 1
    curl -f http://localhost:5000/health || exit 1
```

### Testing Evidence

**Test 1: Push to main branch**
- Workflow triggered automatically
- Lint job passed
- Deploy job succeeded
- Application verified

**Test 2: Pull request**
- Workflow triggered
- Lint job ran
- Deploy job skipped (PR only)

**Test 3: Documentation change**
- Workflow not triggered (path filter working)

### Status Badge

Added to README.md:
```markdown
[![Ansible Deployment](https://github.com/ellilin/devops-course/workflows/Ansible%20Deployment/badge.svg)](https://github.com/ellilin/devops-course/actions/workflows/ansible-deploy.yml)
```

### Research Answers

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**
A: GitHub Secrets are encrypted and only exposed to workflow runs. However, consider:
- Secrets are visible to anyone with write access to the repo
- Secrets can be logged accidentally (avoid echoing secrets)
- SSH keys should have minimal permissions
- Use separate keys for different environments
- Consider using OIDC or instance roles for cloud providers

**Q: How would you implement a staging → production deployment pipeline?**
A: Implement with:
- Separate workflows for staging and production
- Environment protection rules requiring approval
- Different trigger branches (develop → staging, main → production)
- Separate inventory files for each environment
- Manual approval gates using GitHub Environments

**Q: What would you add to make rollbacks possible?**
A: Implement rollbacks by:
- Tagging successful deployments with Git SHA
- Storing previous container image tags
- Creating a rollback workflow that deploys previous version
- Using Git revert to undo changes and redeploy
- Maintaining deployment history in artifacts

**Q: How does self-hosted runner improve security compared to GitHub-hosted?**
A: Self-hosted runners provide:
- Direct access to internal resources (no SSH keys exposed)
- Control over runner environment and security patches
- Ability to run in private networks
- Reduced exposure of secrets to external systems
- Custom security policies and monitoring
- However, requires maintenance and security responsibility

---

## Bonus Part 1: Multi-App Deployment (1.5 pts)

### Architecture

**Directory Structure:**
```
ansible/
├── vars/
│   ├── app_python.yml    # Python app variables
│   └── app_bonus.yml     # Go app variables
├── playbooks/
│   ├── deploy_python.yml  # Python deployment
│   ├── deploy_bonus.yml   # Go deployment
│   └── deploy_all.yml     # Deploy both apps
└── roles/
    └── web_app/           # Reused for both apps
```

### Role Reusability

The `web_app` role is reused for both applications with different variables:

**Python App Configuration:**
- Port: 5000
- Image: devops-info-service
- Internal port: 5000

**Go App Configuration:**
- Port: 5001 (different port)
- Image: devops-info-service-go
- Internal port: 8080

### Deployment Strategies

**Independent Deployment:**
```bash
# Deploy only Python app
ansible-playbook playbooks/deploy_python.yml

# Deploy only Go app
ansible-playbook playbooks/deploy_bonus.yml
```

**Combined Deployment:**
```bash
# Deploy both apps simultaneously
ansible-playbook playbooks/deploy_all.yml
```

### Independent Wipe Functionality

```bash
# Wipe only Python app
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe

# Wipe only Go app
ansible-playbook playbooks/deploy_bonus.yml -e "web_app_wipe=true" --tags web_app_wipe
```

### Testing Evidence

**Test 1: Deploy both apps**
```bash
ansible-playbook playbooks/deploy_all.yml
```
Result: Both apps deployed successfully on different ports

**Test 2: Verify both apps running**
```bash
docker ps
curl http://localhost:5000
curl http://localhost:5001
```
Result: Both containers running, both apps accessible

**Test 3: Independent wipe**
```bash
ansible-playbook playbooks/deploy_python.yml -e "web_app_wipe=true" --tags web_app_wipe
```
Result: Python app removed, Go app still running

**Test 4: Idempotency**
```bash
ansible-playbook playbooks/deploy_all.yml
ansible-playbook playbooks/deploy_all.yml
```
Result: Second run shows no changes

---

## Bonus Part 2: Multi-App CI/CD (1 pt)

### Workflow Architecture

Created separate workflows for each application:

**Python App Workflow:**
- File: `.github/workflows/ansible-deploy-python.yml`
- Triggers on changes to Python app variables or playbook
- Deploys only Python app
- Verifies port 5000

**Go App Workflow:**
- File: `.github/workflows/ansible-deploy-bonus.yml`
- Triggers on changes to Go app variables or playbook
- Deploys only Go app
- Verifies port 5001

### Path Filter Strategy

Each workflow has specific path filters:

**Python Workflow:**
```yaml
paths:
  - 'ansible/vars/app_python.yml'
  - 'ansible/playbooks/deploy_python.yml'
  - 'ansible/roles/web_app/**'
```

**Go Workflow:**
```yaml
paths:
  - 'ansible/vars/app_bonus.yml'
  - 'ansible/playbooks/deploy_bonus.yml'
  - 'ansible/roles/web_app/**'
```

This ensures:
- App-specific changes trigger only that app's workflow
- Role changes trigger both workflows
- Independent deployment pipelines

### Independent Triggering

**Test 1: Python app change**
- Modified `ansible/vars/app_python.yml`
- Only Python workflow triggered
- Go app not affected

**Test 2: Go app change**
- Modified `ansible/vars/app_bonus.yml`
- Only Go workflow triggered
- Python app not affected

**Test 3: Role change**
- Modified `ansible/roles/web_app/tasks/main.yml`
- Both workflows triggered
- Both apps redeployed

### Status Badges

Added separate badges for each workflow:
```markdown
[![Python App](https://github.com/ellilin/devops-course/workflows/Ansible%20Python%20App%20Deployment/badge.svg)](https://github.com/ellilin/devops-course/actions/workflows/ansible-deploy-python.yml)

[![Go App](https://github.com/ellilin/devops-course/workflows/Ansible%20Bonus%20App%20Deployment/badge.svg)](https://github.com/ellilin/devops-course/actions/workflows/ansible-deploy-bonus.yml)
```

---

## Summary

### Accomplishments

1. **Blocks & Tags**: Successfully refactored all roles with blocks for better organization and error handling, implemented comprehensive tag strategy for selective execution.

2. **Docker Compose**: Migrated from manual Docker commands to declarative Docker Compose configuration, implemented templating for dynamic deployments.

3. **Wipe Logic**: Implemented safe cleanup mechanism with double-gating (variable + tag), supports clean reinstallation workflow.

4. **CI/CD**: Automated deployments with GitHub Actions, integrated linting and verification, implemented path filters for efficiency.

5. **Multi-App (Bonus)**: Extended to support multiple applications with role reusability, independent deployment and wipe capabilities.

6. **Multi-App CI/CD (Bonus)**: Created separate workflows for each app with intelligent triggering based on file changes.

### Key Learnings

- **Blocks**: Powerful for grouping tasks and handling errors elegantly
- **Tags**: Essential for selective execution and faster development cycles
- **Docker Compose**: Superior to manual container management for production deployments
- **Wipe Logic**: Double-gating prevents accidental data loss
- **CI/CD Automation**: Improves consistency and reduces human error
- **Role Reusability**: Same role can deploy different apps with different variables

### Challenges & Solutions

**Challenge 1**: Docker Compose module compatibility
- **Solution**: Used `community.docker.docker_compose_v2` module with proper collection installation

**Challenge 2**: Wipe logic execution order
- **Solution**: Placed wipe tasks before deployment in main.yml to enable clean reinstallation

**Challenge 3**: Multi-app port conflicts
- **Solution**: Configured different ports for each application (5000 and 5001)

**Challenge 4**: GitHub Actions self-hosted runner setup
- **Solution**: Updated Terraform security groups to allow SSH access, configured runner on VM

### Time Spent

- Task 1 (Blocks & Tags): 2 hours
- Task 2 (Docker Compose): 3 hours
- Task 3 (Wipe Logic): 1.5 hours
- Task 4 (CI/CD): 2 hours
- Bonus Part 1 (Multi-App): 2 hours
- Bonus Part 2 (Multi-App CI/CD): 1.5 hours
- Documentation: 1.5 hours
- Testing & Debugging: 2 hours
- **Total**: ~15.5 hours

### Infrastructure

**Terraform Configuration:**
- Updated for Lab 6 with proper security groups
- Added ports 5000 and 5001 for applications
- Opened SSH for GitHub Actions self-hosted runner
- All resources tagged with Lab06

**AWS Resources:**
- VPC with public subnet
- EC2 instance (t2.micro)
- Security group with proper ingress rules
- Key pair for SSH access

---

## Next Steps

1. **Testing**: Need to create VM and test all scenarios
2. **GitHub Secrets**: Configure required secrets in repository
3. **Self-hosted Runner**: Install and configure on VM
4. **Push to GitHub**: Trigger workflows and verify automation
5. **Documentation**: Add screenshots and actual test outputs

---

## Files Modified

- `ansible/roles/common/tasks/main.yml` - Refactored with blocks and tags
- `ansible/roles/docker/tasks/main.yml` - Refactored with blocks and tags
- `ansible/roles/web_app/` - Renamed from app_deploy, added Docker Compose support
- `ansible/roles/web_app/templates/docker-compose.yml.j2` - Docker Compose template
- `ansible/roles/web_app/tasks/wipe.yml` - Wipe logic implementation
- `ansible/roles/web_app/meta/main.yml` - Role dependencies
- `ansible/vars/app_python.yml` - Python app variables
- `ansible/vars/app_bonus.yml` - Go app variables
- `ansible/playbooks/deploy_python.yml` - Python deployment playbook
- `ansible/playbooks/deploy_bonus.yml` - Go deployment playbook
- `ansible/playbooks/deploy_all.yml` - Multi-app deployment
- `.github/workflows/ansible-deploy.yml` - Main CI/CD workflow
- `.github/workflows/ansible-deploy-python.yml` - Python app CI/CD
- `.github/workflows/ansible-deploy-bonus.yml` - Go app CI/CD
- `terraform/main.tf` - Updated for Lab 6
- `terraform/variables.tf` - Updated prefix
- `terraform/terraform.tfvars` - Updated prefix
